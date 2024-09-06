import PyPDF2
import io

def extract_text_from_pdf(pdf_content: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    pdf_text = []

    for page in reader.pages:
        content = page.extract_text()
        pdf_text.append(content)
    
    return "\n".join(pdf_text)

def save_text_to_file(text: str, output_file: str):
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(text)

if __name__ == '__main__':
    pdf_file_path = 'demo.pdf'  # Replace with the path to your PDF file
    output_file_path = 'output.txt'  # Replace with the desired output text file name

    text = extract_text_from_pdf(pdf_file_path)
    print(text)
    save_text_to_file(text, output_file_path)

    print(f'Text extracted and saved to {output_file_path}')
