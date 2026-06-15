from fastapi import File, HTTPException, UploadFile
from core.settings import config
import boto3, os
from botocore.exceptions import NoCredentialsError, BotoCoreError
from pathlib import Path
from core.settings import BASE_DIR



aws_access_key = config.AWS_ACCESS_KEY_ID
aws_secret_key = config.AWS_SECRET_ACCESS_KEY
region = config.AWS_REGION
bucket_name = config.BUCKET_NAME




s3_client = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region
)



def s3_upload_pdf(file: UploadFile):
    
    object_key = f"{file}"
    try:
        s3_client.upload_file(file, bucket_name, object_key)
        return {
            "message": f"PDF uploaded successfully!",
            "s3_path": f"s3://{bucket_name}/{object_key}"
        }

    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="AWS credentials not found")
    except BotoCoreError as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        if os.path.exists(file):
            pass



def s3_get_objects(path):
    file_key = f"{path}"
    print("FILE_KEY:", file_key)
    try:
        response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=file_key,
        Delimiter="/pdf"
    )
        files = [obj["Key"] for obj in response.get("Contents", [])]
        return {"files": files}
    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="AWS credentials not found")
    except s3_client.exceptions.NoSuchKey:
        return {"error": f"File '{file_key}' not found in bucket '{bucket_name}'."}
    except BotoCoreError as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") 
         




def get_presigned_urls(url):
    file_key = f"{url}"
    print("url", file_key)
    url = s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket_name,
            'Key': file_key  
        },
        ExpiresIn=3600  
    )

    print("Download URL:", url)
    return url




def s3_create_project_folder(path:str, description:str):
    object_key = f"{path}"
    try:
        s3_client.put_object(Bucket = bucket_name, Key = object_key)
        return {
            "message": f"Project created successfully!",
            "s3_path": f"s3://{bucket_name}/{object_key}"
        }

    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="AWS credentials not found")
    except BotoCoreError as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    




def s3_get_folders(path):
    file_key = f"{path}"
    print("FILE_KEY:", file_key)
    try:
        response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=file_key,
        Delimiter="/"
    )
        project_folders = [obj["Key"] for obj in response.get("Contents", [])]
        return {"project": project_folders}
    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="AWS credentials not found")
    except s3_client.exceptions.NoSuchKey:
        return {"error": f"File '{file_key}' not found in bucket '{bucket_name}'."}
    except BotoCoreError as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")     





def s3_download_pdf(s3_pdf_path):
    path = get_presigned_urls(s3_pdf_path)
    save_path = f"{BASE_DIR}/s3_downloads"
    print("SAVE PATH", save_path)
    os.makedirs(save_path,exist_ok=True)
    file_path = os.path.join(save_path, "downloaded.pdf")
    s3_client.download_file(bucket_name, s3_pdf_path, str(file_path))   

    return file_path





def s3_get_all_files(path):
    file_key = f"{path}"
    print("FILE_KEY:", file_key)
    try:
        response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=file_key,
        Delimiter=""
    )
        project_folders = [obj["Key"] for obj in response.get("Contents", [])]
        return {"project": project_folders}
    except NoCredentialsError:
        raise HTTPException(status_code=403, detail="AWS credentials not found")
    except s3_client.exceptions.NoSuchKey:
        return {"error": f"File '{file_key}' not found in bucket '{bucket_name}'."}
    except BotoCoreError as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")     
    