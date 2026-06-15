from google.cloud import storage
from google.oauth2 import service_account
from core.settings import config
from fastapi import UploadFile, File, HTTPException
from io import BytesIO
from fastapi.responses import StreamingResponse
from datetime import timedelta
from core.settings import BASE_DIR
import os, re
from google.api_core.exceptions import NotFound, GoogleAPIError
from google.api_core.exceptions import NotFound as GCPNotFound
from typing import Dict
from typing import List
import logging
import fitz  




GOOGLE_APPLICATION_CREDENTIALS = config.GOOGLE_APPLICATION_CREDENTIALS
GCP_BUCKET_NAME = config.GCP_BUCKET_NAME
credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)

client = storage.Client(credentials=credentials)

BUCKET_NAME = GCP_BUCKET_NAME
bucket = client.bucket(BUCKET_NAME)




def create_folder(folder_name: str, description: str):
    """
    Creates a REAL GCP folder by uploading test.txt + placeholder.
    This guarantees the folder appears in .prefixes
    """
    
    if not folder_name.endswith('/'):
        folder_name += '/'

    try:
        test_txt_path = folder_name + 'test.txt'
        test_blob = bucket.blob(test_txt_path)
        test_blob.upload_from_string(description, content_type='text/plain')
        print(f"[GCP] Created: {test_txt_path}")

        
        placeholder = bucket.blob(folder_name)  # e.g., "users/123/MyProject/"
        placeholder.upload_from_string('', content_type='application/octet-stream')
        print(f"[GCP] Placeholder: {folder_name}")

        return {"message": f"Folder '{folder_name}' created successfully."}

    except Exception as e:
        print(f"[GCP ERROR] Failed to create folder {folder_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")




def upload_pdf_file(file: UploadFile):
    path = f"{file}"
    blob = bucket.blob(path)
    with open(path, 'rb') as file_data:
        blob.upload_from_file(file_data, content_type='application/pdf')

    return {"message": f"File '{path}' uploaded."}




def upload_pdf_from_path(local_path: str):
    """
    Upload a local PDF file to GCP bucket using the same path structure.
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")

    blob = bucket.blob(local_path) 
    blob.upload_from_filename(local_path, content_type='application/pdf')
    print(f"[GCP] PDF uploaded: {local_path}")
    return {"message": f"File '{local_path}' uploaded successfully."}




def upload_csv_file(path:str , file):
    path = f"{path}"
    blob = bucket.blob(path)
    blob.upload_from_string(file, content_type="text/csv")
    return {"message": f"File '{path}' uploaded."}




def upload_text_file(path:str, file:str):
    path = f"{path}"
    blob = bucket.blob(path)
    try:
        blob.upload_from_string(file, content_type="text/plain")
    except Exception as e:
        raise HTTPException(402, detail=str(e))    
    return {"message": f"File '{path}' uploaded."}




def upload_image_file(file: UploadFile, extention:str):
    path = f"{file}"
    blob = bucket.blob(path)
    content_type = ""
    if extention == "png":
        content_type = "image/png"
    elif extention == "jpeg":
        content_type = "image/jpeg"
    elif extention == "jpg":
        content_type = "image/jpg"

    with open(path, 'rb') as file_data:
        blob.upload_from_file(file_data, content_type=content_type)
    return {"message": f"File '{path}' uploaded."}




def download_pdf_file(path: str):
    blob = bucket.blob(path)

    if not blob.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    save_path = f"{BASE_DIR}/s3_downloads"
    print("SAVE PATH", save_path)
    os.makedirs(save_path,exist_ok=True)

    destination_file = os.path.join(save_path, "downloaded.pdf")
    blob.download_to_filename(destination_file)

    return destination_file




def generate_presigned_url(blob_name: str, expiration: timedelta = timedelta(minutes=15)):
    bucket = client.get_bucket(BUCKET_NAME) 
    blob = bucket.blob(blob_name)
    url = blob.generate_signed_url(
        expiration=expiration,  
        method="GET",            
        version="v4"             
    )
    return url




def get_project_names_only(path: str):
    """
    Returns only direct project folder names.
    """
    if not path.endswith('/'):
        path += '/'

    print(f"[DEBUG] Listing folders with prefix: {path}")

    try:
        blobs = bucket.list_blobs(prefix=path, delimiter='/')
        
        print(f"[DEBUG] Found {len(list(blobs))} blobs")
        print(f"[DEBUG] Prefixes: {list(blobs.prefixes)}")

        project_names = []
        for prefix in blobs.prefixes:
            folder_name = prefix[len(path):].rstrip('/')
            if folder_name:
                project_names.append(folder_name)
                print(f"[DEBUG] Found project: {folder_name}")

        print(f"[DEBUG] Returning projects: {project_names}")
        return project_names

    except Exception as e:
        print(f"[GCP ERROR] list_blobs failed: {e}")
        return []




def get_all_files_and_folders_in_project(path: str) -> Dict:
    if not path.endswith('/'):
        path += '/'

    try:
        blobs = bucket.list_blobs(prefix=path)
        folders = set()
        files_by_folder = {}

        for blob in blobs:
            relative_path = blob.name[len(path):]
            if not relative_path or relative_path == 'test.txt':
                continue

            relative_path = re.sub(r'\\+', '/', relative_path)
            relative_path = re.sub(r'/+', '/', relative_path)

            parts = relative_path.split('/')
            if len(parts) == 1:
                folder = ""
                filename = parts[0]
            else:
                folder = parts[0] + '/'
                filename = '/'.join(parts[1:])

            if folder:
                folders.add(folder)

            if folder not in files_by_folder:
                files_by_folder[folder] = []
            if filename:
                files_by_folder[folder].append(filename)

        folder_list = sorted(list(folders))
        total_files = sum(len(files) for files in files_by_folder.values())

        return {
            "folders": folder_list,
            "files": files_by_folder,
            "stats": {
                "total_files": total_files,
                "total_folders": len(folder_list)
            }
        }

    except Exception as e:
        print(f"[GCP ERROR] Failed to list project contents: {e}")
        return {"folders": [], "files": {}, "stats": {"total_files": 0, "total_folders": 0}}





def move_file(source_path: str, destination_folder: str, reason: str):
    """
    Move a file + its .txt metadata to a new folder (exclude/include)
    destination_folder must be the FOLDER path (e.g. .../includes/google_scholar/covid/)
    """
    try:
        source_path = re.sub(r'\\+', '/', source_path.strip('/'))
        destination_folder = re.sub(r'\\+', '/', destination_folder.strip('/'))
        if not destination_folder.endswith('/'):
            destination_folder += '/'

        source_blob = bucket.blob(source_path)
        if not source_blob.exists():
            raise HTTPException(status_code=404, detail=f"Source file not found: {source_path}")

        filename = os.path.basename(source_path)
        dest_file_path = destination_folder + filename
        bucket.copy_blob(source_blob, bucket, dest_file_path)
        meta_src = os.path.splitext(source_path)[0] + ".txt"
        meta_dst = os.path.splitext(dest_file_path)[0] + ".txt"
        meta_blob = bucket.blob(meta_src)
        if meta_blob.exists():
            bucket.copy_blob(meta_blob, bucket, meta_dst)

        reason_path = os.path.splitext(dest_file_path)[0] + "_REASON.txt"
        bucket.blob(reason_path).upload_from_string(reason, content_type="text/plain")

        source_blob.delete()
        if meta_blob.exists():
            meta_blob.delete()

        return {
            "message": "File moved successfully",
            "new_path": dest_file_path
        }

    except Exception as e:
        print(f"[MOVE ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))




def add_reason_to_filename(filename: str) -> str:
    return re.sub(r'(_\d+)(\.txt)$', r'_REASON\1\2', filename)





def delete_file(file_path: str):
    print(f"[GCP DELETE] Attempting to delete: {file_path}")

    blob = bucket.blob(file_path)
    meta_path = f"{os.path.splitext(file_path)[0]}.txt"
    meta_blob = bucket.blob(meta_path)
    reason_path = f"{os.path.splitext(file_path)[0]}_REASON.txt"
    reason_blob = bucket.blob(reason_path)

    deleted = []
    if blob.exists():
        blob.delete()
        deleted.append(file_path)
    if meta_blob.exists():
        meta_blob.delete()
        deleted.append(meta_path)
    if reason_blob.exists():
        reason_blob.delete()
        deleted.append(reason_path)

    if not deleted:
        raise HTTPException(status_code=404, detail="Requested file not found!")

    return {"message": "File and related metadata deleted", "deleted": deleted}





def undo_file(source_path: str, destination_folder: str):
    try:
        source_path = re.sub(r'\\+', '/', source_path.strip('/'))

        if not destination_folder.endswith('/'):
            destination_folder += '/'

        src_blob = bucket.blob(source_path)
        if not src_blob.exists():
            raise HTTPException(status_code=404, detail=f"Requested file not found: {source_path}")

        filename = os.path.basename(source_path)
        dest_file_pdf = destination_folder + filename
        dest_file_txt = destination_folder + os.path.splitext(filename)[0] + ".txt"

        bucket.copy_blob(src_blob, bucket, dest_file_pdf)

        meta_blob = bucket.blob(os.path.splitext(source_path)[0] + ".txt")
        if meta_blob.exists():
            bucket.copy_blob(meta_blob, bucket, dest_file_txt)

        src_blob.delete()
        if meta_blob.exists():
            meta_blob.delete()

        reason_blob = bucket.blob(os.path.splitext(source_path)[0] + "_REASON.txt")
        if reason_blob.exists():
            reason_blob.delete()

        return {
            "message": "File restored successfully",
            "new_path": dest_file_pdf
        }

    except Exception as e:
        print(f"[UNDO ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))





async def view_content(file_path: str):
    """
    Reads content of PDF or plain text files (.txt metadata files)
    Returns extracted text + metadata
    """
    file_path = re.sub(r'\\+', '/', file_path.strip('/'))
    blob = bucket.blob(file_path)

    if not blob.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    try:
        file_bytes = blob.download_as_bytes()
        file_name = os.path.basename(file_path).lower()

        
        if file_name.endswith('.txt'):
            content = file_bytes.decode('utf-8')
            return {
                "file_name": os.path.basename(file_path),
                "content": content,
                "metadata": {"type": "metadata", "format": "text"},
                "extracted_successfully": True
            }

        
        if file_name.endswith('.pdf'):
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text("text") + "\n"

            metadata = doc.metadata
            clean_metadata = {}
            for k, v in metadata.items():
                if v and str(v).strip():
                    clean_metadata[k] = str(v).strip()

            page_count = len(doc)
            doc.close()

            return {
                "file_name": os.path.basename(file_path),
                "content": text.strip(),
                "metadata": clean_metadata or {"title": "Unknown"},
                "page_count": page_count,
                "extracted_successfully": True
            }

        raise HTTPException(status_code=400, detail="Unsupported file type. Only .pdf and .txt are allowed.")

    except Exception as e:
        logging.error(f"[VIEW_CONTENT ERROR] {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")





def delete_folder(folder_path: str) -> bool:
    """
    Recursively delete a folder and ALL its contents from GCP bucket.
    
    Args:
        folder_path (str): Path like "users/123/my-project/"
    
    Returns:
        bool: True if folder existed and was deleted, False if not found.
    """
    try:
        if not folder_path.endswith('/'):
            folder_path += '/'

        blobs = list(bucket.list_blobs(prefix=folder_path))
        
        if not blobs:
            logging.info(f"Folder not found: {folder_path}")
            return False 

        for blob in blobs:
            try:
                blob.delete()
                logging.debug(f"Deleted blob: {blob.name}")
            except Exception as e:
                logging.error(f"Failed to delete {blob.name}: {e}")

        logging.info(f"Successfully deleted folder: {folder_path}")
        return True

    except GCPNotFound:
        logging.info(f"Folder not found (GCPNotFound): {folder_path}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error deleting folder {folder_path}: {e}")
        return False





async def list_files_in_folder(prefix: str) -> List[str]:
    """
    List all file blob names under a given prefix (folder).
    Returns full blob names (e.g. users/123/project/google_scholar/topic/file.pdf)

    Args:
        prefix (str): Folder path, e.g. "users/123/myproject/google_scholar/"

    Returns:
        List[str]: List of full blob names (files only, no folders)
    """
    if not prefix.endswith("/"):
        prefix += "/"

    try:
        blobs = bucket.list_blobs(prefix=prefix)
        file_paths = []

        for blob in blobs:
            if blob.name.endswith("/") or blob.name.endswith("test.txt"):
                continue
            file_paths.append(blob.name)

        logging.debug(f"[GCP LIST] Found {len(file_paths)} files in {prefix}")
        return file_paths

    except Exception as e:
        logging.error(f"[GCP LIST ERROR] Failed to list files in {prefix}: {e}")
        return []





async def download_text_file(blob_name: str) -> str:
    """
    Download a .txt metadata file as string.

    Args:
        blob_name (str): Full path to .txt file in bucket

    Returns:
        str: Content of the text file

    Raises:
        HTTPException 404 if not found
    """
    blob_name = blob_name.strip("/")
    blob = bucket.blob(blob_name)

    if not blob.exists():
        raise HTTPException(status_code=404, detail=f"Metadata file not found: {blob_name}")

    try:
        content = blob.download_as_text(encoding="utf-8")
        return content
    except Exception as e:
        logging.error(f"[GCP DOWNLOAD TEXT ERROR] {blob_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read metadata: {str(e)}")
    




def upload_pdf_from_bytes(gcp_path: str, pdf_bytes: bytes):
    """
    Upload raw PDF bytes directly to GCP (preserves binary integrity)
    """
    gcp_path = gcp_path.replace("\\", "/")
    blob = bucket.blob(gcp_path)
    blob.upload_from_string(pdf_bytes, content_type='application/pdf')
    print(f"[GCP] PDF uploaded (bytes): {gcp_path}")
    return {"message": f"File '{gcp_path}' uploaded successfully."}