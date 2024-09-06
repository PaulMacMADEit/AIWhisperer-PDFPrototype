from typing import List, Tuple
import openai
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from typing import Union
from datetime import date
from prompts import Structured_Prompt, Summarize_Prompt

import modal 
import csv

app = modal.App(name="chat_model_app", image=modal.Image.debian_slim().pip_install("openai", "anthropic"))

# Context limits for different models
CONTEXT_LIMITS = {
    "OpenAI-GPT4": 128000,
    "Anthropic-Sonnet3.5": 200000,
    "Google-Gemini1.5": 1000000
}

class RoomInfo(BaseModel):
    sample_group: str
    supplier: str
    property: str
    item: str
    room_config: str
    season_start_date: str  # Change to str
    season_end_date: str  # Change to str
    item_max_pax: int
    price_rrp_adult_cost: float
    item_id: int
    item_per_person: bool
    is_item_live: bool
    is_room_config_active: bool
    property_id: int
    property_address: str
    is_property_active: bool
    supplier_id: int
    supplier_address: str
    is_supplier_active: bool
    season_type: str
    season: str
    is_season_monday: bool
    is_season_tuesday: bool
    is_season_wednesday: bool
    is_season_thursday: bool
    is_season_friday: bool
    is_season_saturday: bool
    is_season_sunday: bool
    is_season_deleted: bool
    min_days: int
    max_days: int
    price_adj_adult_cost: float
    is_price_live: bool
    is_price_deleted: bool

class TableOutput(BaseModel):
    rooms: List[RoomInfo]


text_chunk = "Your text chunk here"
custom_prompt = "You are a helpful assistant"

def LLM_Model(text: str, model: str) -> str:
    extracted_text = ""
    
    if model == "OpenAI-GPT4":
        chunks = chunk_text(text, CONTEXT_LIMITS[model])
        for chunk in chunks:
            completion = OpenAI.remote(Summarize_Prompt, chunk)
            extracted_text += completion
        
    
    elif model == "Anthropic-Sonnet3.5":
        print("Using Anthropic-Sonnet3.5")
        chunks = chunk_text(text, CONTEXT_LIMITS[model])
        for chunk in chunks:
            completion = Anthropic.remote(chunk, Summarize_Prompt)
            print(completion)
            extracted_text += completion
    
    elif model == "OpenAI_Structured":
        print("Using OpenAI-GPT4 with structured output")
        completion = OpenAI.remote(Structured_Prompt, text, use_structured_output=True, output_schema=TableOutput)
        extracted_text = completion
        
    elif model == "Google-Gemini1.5":
        print("Using Google-Gemini1.5")
    
    return extracted_text 

def chunk_text(text: str, chunk_size: int) -> List[str]:
    chunks = []
    current_chunk = ""
    
    for paragraph in text.split('\n'):
        if len(current_chunk) + len(paragraph) + 1 <= chunk_size:
            current_chunk += paragraph
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    print("Number of chunks: " + str(len(chunks)))
    return chunks

@app.function(secrets=[modal.Secret.from_name("OpenAI_API_Key")], container_idle_timeout=300)
def OpenAI(system_prompt: str, message_content: str, use_structured_output=False, output_schema: Optional[type[BaseModel]] = None):
    from openai import OpenAI
    import time
    client = OpenAI()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message_content}
    ]
    start_time = time.time()
    
    if use_structured_output and output_schema:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=messages,
            response_format=output_schema,
        )
        result = completion.choices[0].message.parsed
    else:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-4o-2024-08-06",
        )
        result = chat_completion.choices[0].message.content
    
    end_time = time.time()
    latency = end_time - start_time
    print(f"OpenAI API request latency: {latency:.2f} seconds")
    
    return result

@app.function(secrets=[modal.Secret.from_name("Anthropic-API")], container_idle_timeout=300)
def Anthropic(context, query):
    import anthropic

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[{"role": "user", "content": query + "\n\n" + context}],
    )
    return [block.text for block in message.content]

@app.local_entrypoint()
def main():
    print("Running API tests:")

    test = False
    if test:
        #OpenAI
        prompt= "What is 1+1? Be very concise."
        #completion = complete_text.remote(prompt)
        completion = OpenAI.remote(prompt)
        print("OpenAI: " + prompt + ": " + completion)
        
        #Anthropic
        query = "What is 1+1?"
        context = "Be very concise."
        completion = Anthropic.remote(prompt, query)
        print("Anthropic: " + query + ": " + " ".join(completion))
    
    text = "The property is in NSW, it is 200 acres with rolling hills and a creek. Has a 2 queen bedroom, $165/night, extra toilets, and wifi via starlink"
    result = extract_with_model(text, "OpenAI-GPT4")
    
    table_result = OpenAI.remote(result, use_structured_output=True, output_schema=TableOutput)
    #print("Table Output: ", table_result)

    # Save the result to a CSV file
    save_to_csv(table_result)

def save_to_csv(table_output: TableOutput, filename: str = "room_info.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=RoomInfo.__annotations__.keys())
        writer.writeheader()
        for room in table_output.rooms:
            writer.writerow(room.model_dump())
    print(f"Data saved to {filename}")