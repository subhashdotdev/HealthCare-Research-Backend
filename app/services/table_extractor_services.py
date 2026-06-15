import base64, requests, csv, zipfile, os
from pdf2image import convert_from_bytes
from io import BytesIO, StringIO
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import UploadFile, Request
from core.utils.aws_utils import bucket_name, s3_client
from schemas.extractors_schemas import TableExtractorRequest
from core.utils.gcp_utils import upload_csv_file



load_dotenv(override=True)



api_key=os.getenv('OPENAI_API_KEY')




async def extract_tables(request:Request,project_name:str,file:UploadFile):
    user_id = request.state.user.get("user_id")
    project_name = project_name
    dir = f"users/{user_id}/{project_name}/csv"
    name = file.filename
    pdf_bytes = await file.read()
    images = convert_from_bytes(pdf_bytes)
    extracted_data = []
    csv_buffers = []

    for i, image in enumerate(images):
        img_bytes = BytesIO()
        image.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        extracted_table = extract_tables_from_image(img_bytes.read())

        if extracted_table and extracted_table.strip() != "No table found.":
            print(f"Extracted Table from page {name}{i+1}:")
            print(extracted_table)
            key = f"{dir}/{name}_{i+1}.csv"
            csv_buffer = StringIO()
            csv_writer = csv.writer(csv_buffer)

            table_lines = extracted_table.split('\n')
            for line in table_lines:
                if line.strip(): 
                    csv_writer.writerow([cell.strip() for cell in line.split('|')])
            
            csv_buffers.append((f"{name}_{i+1}.csv", csv_buffer))
            upload_csv_file(path=key,file=csv_buffer.getvalue() )
        else:
            print(f"No table detected on page {name}{i + 1}.")
    return {"message": "Csv file extracted successfully!"}





def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')





def extract_tables_from_image(image_bytes):
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    content_text = (
        "Please analyze the image provided and extract all tables contained within it. "
        "If there are no tables, respond with 'no table found'. "
        "If there are multiple tables, extract each table separately and clearly label them. "
        "Be meticulous to avoid missing any rows or columns."
    )

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": content_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 800
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_data = response.json()

    if response.status_code != 200:
        print(f"Error: {response_data}")
        return None
    else:
        return response_data['choices'][0]['message']['content']
