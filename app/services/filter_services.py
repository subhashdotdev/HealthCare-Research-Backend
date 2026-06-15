
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from schemas.filter_schemas import ExcludeFileRequest, IncludeFileRequest, DeleteDownloadedFileRequest, UndoFileRequest, ViewContentRequest
from core.utils.gcp_utils import move_file, delete_file, undo_file, view_content
import os
import re



def _clean_path(path: str) -> str:
    """
    Normalize path:
    - Replace all backslashes with forward slashes
    - Handle cases like 'folder\\file.pdf' → 'folder/file.pdf'
    - Strip leading/trailing slashes
    """
    if not path:
        return ""
    normalized = re.sub(r'\\+', '/', path)  
    normalized = re.sub(r'/+', '/', normalized) 
    return normalized.strip('/')






def _extract_download_source(file_path: str) -> str:
    """
    Extract the source (pubmed/google_scholar/google_scholer) from file_path
    Expected: users/{id}/{project}/google_scholar/.../file.pdf
    But we get relative: google_scholar/.../file.pdf
    """
    parts = [p for p in file_path.split('/') if p]
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid file path: too short")
    
    return parts[0] 





def exclude_specific_file(request: Request, data: ExcludeFileRequest):
    user_id = request.state.user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    project_name = data.project_name
    topic = data.topic or ""
    raw_source_path = data.file_path
    reason = data.reason or "Excluded by user"

    
    source_path = _clean_path(raw_source_path)
    if not source_path:
        raise HTTPException(status_code=400, detail="Invalid file path")

    file_name = os.path.basename(source_path)

    
    parts = source_path.split('/')
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid path structure")

    original_source = parts[0]  
    original_topic = parts[1]   
    
    full_source_path = f"users/{user_id}/{project_name}/{original_source}/{original_topic}/{file_name}"

    
    destination_folder = f"users/{user_id}/{project_name}/excludes/{original_source}/{original_topic}/"

    print(f"[EXCLUDE] Moving:\n  {full_source_path}\n  → {destination_folder}")

    
    return move_file(
        source_path=full_source_path,
        destination_folder=destination_folder,
        reason=reason
    )




def include_specific_file(request: Request, data: IncludeFileRequest):
    user_id = request.state.user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    project_name = data.project_name
    raw_source_path = data.file_path
    reason = data.reason or "Included by user"

    source_path = _clean_path(raw_source_path)
    if not source_path:
        raise HTTPException(status_code=400, detail="Invalid file path")

    
    parts = [p for p in source_path.split('/') if p]
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid source path structure")

    download_source = parts[0]                    
    original_topic_folder = parts[1]             

    full_source_path = f"users/{user_id}/{project_name}/{source_path}"
    destination_folder = f"users/{user_id}/{project_name}/includes/{download_source}/{original_topic_folder}/"

    print(f"[INCLUDE] Moving:\n  {full_source_path}\n  → {destination_folder}")

    return move_file(
        source_path=full_source_path,
        destination_folder=destination_folder,
        reason=reason
    )










def undo_specific_file(data: UndoFileRequest, request: Request):
    user_id = request.state.user.get("user_id")
    project_name = data.project_name

    rel_path = _clean_path(data.file_path)
    parts = rel_path.split('/')

    if "includes" in parts:
        base_idx = parts.index("includes")
    elif "excludes" in parts:
        base_idx = parts.index("excludes")
    else:
        raise HTTPException(status_code=400, detail="Invalid undo path: neither 'includes' nor 'excludes' folder found")

    try:
        original_source = parts[base_idx + 1]  
        original_topic = parts[base_idx + 2]   
    except IndexError:
        raise HTTPException(status_code=400, detail="Invalid undo path structure: missing source/topic")

    filename = os.path.basename(rel_path)

    destination_folder = f"users/{user_id}/{project_name}/{original_source}/{original_topic}/"
    full_source_path = f"users/{user_id}/{project_name}/{rel_path}"

    print(f"[UNDO] Restoring:\n  {full_source_path}\n  → {destination_folder}")

    return undo_file(
        source_path=full_source_path,
        destination_folder=destination_folder
        
    )







def delete_downloaded_file(request: Request, data: DeleteDownloadedFileRequest):
    """
    Delete a file + its metadata + reason file.
    `data.file_path` is the *relative* path shown in the UI.
    """
    user_id = request.state.user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    project_name = data.project_name
    rel_path = _clean_path(data.file_path)          
    if not rel_path:
        raise HTTPException(status_code=400, detail="Invalid file path")

    full_path = f"users/{user_id}/{project_name}/{rel_path}"
    print(f"[DELETE] Full path: {full_path}")

    return delete_file(full_path)   





async def view_file_content(data: ViewContentRequest, request: Request):
    user_id = request.state.user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    project_name = data.project_name
    relative_path = data.file_path  

    relative_path = _clean_path(relative_path)
    full_path = f"users/{user_id}/{project_name}/{relative_path}"

    print(f"[VIEW_CONTENT] Full GCS path: {full_path}")

    try:
        return await view_content(file_path=full_path)
    except HTTPException as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {full_path}"
            )
        raise

