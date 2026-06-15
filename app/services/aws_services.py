from core.utils.aws_utils import s3_get_objects, s3_create_project_folder, s3_get_folders, get_presigned_urls
from fastapi import Request, HTTPException
from schemas.project_schemas import CreateNewProjectRequest, DownloadArticles
from core.utils.gcp_utils import create_folder, get_project_names_only, generate_presigned_url, delete_folder
 



def subfolders_list(path:str):
    return s3_get_objects(path)



def create_new_project(request:Request, data: CreateNewProjectRequest):
    user_id = request.state.user.get("user_id")
    folder_name = data.project_name
    project_description = data.project_description
    path = f"users/{user_id}/{folder_name}"
    return create_folder(folder_name=path, description=project_description)




def existing_project_list(request:Request):
    user_id = request.state.user.get("user_id")
    path = f"users/{user_id}/"
    return get_project_names_only(path=path)





# def download_article(request:Request, data:DownloadArticles):
#     path = data.path
#     print("PATH:", path)
#     return generate_presigned_url(path)



def download_article(request: Request, data: DownloadArticles):
    user_id = request.state.user.get("user_id")
    # Build full GCP path
    full_path = f"users/{user_id}/{data.project_name}/{data.path}"
    print("FINAL PATH USED FOR DOWNLOAD:", full_path)
    return generate_presigned_url(full_path)




def delete_project(request: Request, project_name: str):
    user_id = request.state.user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    folder_path = f"users/{user_id}/{project_name}/"
    success = delete_folder(folder_path)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_name}' not found or already deleted.")
    
    return {
        "detail": f"Project '{project_name}' and all its contents deleted successfully."
    }