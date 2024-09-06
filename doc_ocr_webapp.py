from pathlib import Path
import fastapi
import fastapi.staticfiles
import modal
from ExtractPDF_Text import *
from modal import Image
from ChatModel import app as chat_model_app, LLM_Model
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import csv
import io
from fastapi.responses import StreamingResponse
import json
from prompts import Structured_Prompt, Summarize_Prompt

current_dir = Path(__file__).parent

image = Image.debian_slim().pip_install("PyPDF2", "openai", "anthropic", "jinja2")
app = modal.App("example-doc-ocr-webapp")
app.include(chat_model_app)
web_app = fastapi.FastAPI()
templates = Jinja2Templates(directory="templates")

@web_app.post("/parse")
async def parse(request: fastapi.Request, container_idle_timeout=300, keep_warm=2):
    print("Step 1: Extract text from PDF")
    form = await request.form()
    file = form.get("file")
    
    if file is None:
        raise fastapi.HTTPException(status_code=400, detail="No file uploaded")
    
    contents = await file.read()
    text = extract_text_from_pdf(contents)

    print("Extracted Text: ", text[:100], "...\n")
    
    full_transcript_path = Path("full_transcripts") / f"{file.filename}.txt"
    full_transcript_path.parent.mkdir(exist_ok=True)
    with open(full_transcript_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    print("Step 2: Condense Text. \n")
    extracted_text = LLM_Model(text, "OpenAI-GPT4")
    
    print("Step 3: Produce Table. \n")
    table_result = LLM_Model(extracted_text, "OpenAI_Structured")

    # Convert table_result to a string representation
    table_result_str = str(table_result)
    print("Table Output: ", table_result_str[:100])
    
    # Convert TableOutput to dictionary
    table_result_dict = {"rooms": [room.dict() for room in table_result.rooms]}
    
    # Save the table result to a file
    table_data_path = Path("table_data") / f"{file.filename}.json"
    table_data_path.parent.mkdir(exist_ok=True)
    with open(table_data_path, "w", encoding="utf-8") as f:
        json.dump(table_result_dict, f, ensure_ascii=False, indent=2)
    
    return {
        "filename": file.filename,
        "text": extracted_text,
        "table": table_result_dict,
    }

@web_app.get("/result/{call_id}")
async def poll_results(call_id: str):
    print("call_id: ", call_id)
    result = "I am a test result"
    return result

assets_path = Path(__file__).parent / "doc_ocr_frontend"

@app.function(
    mounts=[
        modal.Mount.from_local_dir(assets_path, remote_path="/assets"),
        modal.Mount.from_local_dir(current_dir, remote_path="/root")
    ],
    image=image
)

@modal.asgi_app()
def wrapper():
    web_app.mount(
        "/", fastapi.staticfiles.StaticFiles(directory="/assets", html=True)
    )
    return web_app

@web_app.get("/full_transcript/{filename}")
async def get_full_transcript(filename: str):
    full_transcript_path = Path("full_transcripts") / f"{filename}.txt"
    if not full_transcript_path.exists():
        raise fastapi.HTTPException(status_code=404, detail="Transcript not found")
    
    with open(full_transcript_path, "r", encoding="utf-8") as f:
        full_text = f.read()
    
    return {"filename": filename, "text": full_text}


@web_app.get("/download_csv/{filename}")
async def download_csv(filename: str):
    table_data_path = Path("table_data") / f"{filename}.json"
    if not table_data_path.exists():
        raise fastapi.HTTPException(status_code=404, detail="Table data not found")
    
    with open(table_data_path, "r", encoding="utf-8") as f:
        table_data = json.load(f)
    
    # Create a CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    if table_data and "rooms" in table_data and table_data["rooms"]:
        headers = table_data["rooms"][0].keys()
        writer.writerow(headers)
    
    # Write data
    for room in table_data["rooms"]:
        writer.writerow(room.values())
    
    # Create a StreamingResponse with the CSV content
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}_table_data.csv"
    
    return response