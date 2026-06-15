from io import BytesIO
import os
from pdf2image import convert_from_bytes
from services.image_extractor_services import extract_images_from_pdf, download_image
from services.table_extractor_services import extract_tables_from_image
import zipfile, csv
from io import StringIO
from fastapi import UploadFile, Request
from core.utils.aws_utils import bucket_name, s3_client
from core.utils.gcp_utils import upload_csv_file




async def extract_table_and_image(request:Request, project_name:str, file: UploadFile):
    user_id = request.state.user.get("user_id")
    print("user_id", user_id)
    project_name = project_name
    dir = f"users/{user_id}/{project_name}"
    pdf_bytes = await file.read()
    file_name = os.path.splitext(file.filename)[0]
    img_dir = os.path.join(dir,"pdfImages", file_name)
    csv_dir = f"{dir}/csv"

    images = await extract_images_from_pdf(pdf_bytes, img_dir)
    if images:
        print("HIIIIIIIIIII")

    images_for_tables = convert_from_bytes(pdf_bytes)
    csv_buffers = []

    for i, image in enumerate(images_for_tables):
        img_bytes = BytesIO()
        image.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        extracted_table = extract_tables_from_image(img_bytes.read())

        if extracted_table and extracted_table.strip() != "No table found.":
            print(f"Extracted Table from page {i + 1}:")
            print(extracted_table)
            key = f"{csv_dir}/extracted_table_page_{i + 1}.csv" 
            csv_buffer = StringIO()
            csv_writer = csv.writer(csv_buffer)

            table_lines = extracted_table.split('\n')
            for line in table_lines:
                if line.strip():
                    csv_writer.writerow([cell.strip() for cell in line.split('|')])

            csv_buffers.append((f"extracted_table_page_{i + 1}.csv", csv_buffer))
            upload_csv_file(path=key,file=csv_buffer.getvalue())
        else:
            print(f"No table detected on page {i + 1}.")
    return {"message": "Combined extraction done!"}
