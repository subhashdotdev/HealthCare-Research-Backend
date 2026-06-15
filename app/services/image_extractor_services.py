import fitz  
from io import BytesIO
import os
from core.settings import INPUT_DIR
from fastapi import UploadFile, Request
from core.utils.aws_utils import s3_upload_pdf, get_presigned_urls
from core .utils.gcp_utils import upload_image_file




async def extract_images(request: Request,project_name:str, file:UploadFile):
    user_id = request.state.user.get("user_id")
    project_name = project_name
    print("USER_id",user_id)
    dir = f"users/{user_id}/{project_name}"
    file_name = os.path.splitext(file.filename)[0]
    save_dir = os.path.join(dir, "pdfImages", file_name)
    print(f"Processing the PDF file and saving images to: {save_dir}")
    content = await file.read()
    images = await extract_images_from_pdf(content, save_dir)
    return images





async def extract_images_from_pdf(pdf_file, save_dir):
    doc = fitz.open(stream= pdf_file, filetype="pdf")
    images = []
    presigned_urls = []
    os.makedirs(save_dir, exist_ok=True)

    for page_num in range(doc.page_count):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list, start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image["image"]
            img_ext = base_image["ext"]
            img_name = f"image_{page_num + 1}_{img_index}.{img_ext}"
            img_path = os.path.join(save_dir, img_name)
            with open(img_path, "wb") as f:
                f.write(img_bytes)

            result = upload_image_file(img_path, img_ext)
            print("Result:", result)  
            images.append({
                "page_num": page_num + 1,
                "img_index": img_index,
                "img_bytes": img_bytes,
                "img_ext": img_ext,
                "img_path": img_path
            })
            presigned_urls.append (get_presigned_urls(img_path)) 
    return presigned_urls





def download_image(image_bytes, ext, page_num, img_index):
    img_name = f"image_{page_num}_{img_index}.{ext}"
    buffer = BytesIO(image_bytes)
    return {
        "label" : f"Download Image {page_num}_{img_index}",
        "data" : buffer,
        "file_name" : img_name,
        "mime" : f"image/{ext}"
    }

