from pydantic import BaseModel



class ExcludeFileRequest(BaseModel):
    file_path: str
    reason: str
    topic: str
    project_name: str



class ExcludeFileResponse(BaseModel):
    message: str



class IncludeFileRequest(BaseModel):
    file_path: str
    reason: str
    project_name: str
    topic: str



class IncludeFileResponse(BaseModel):
    message: str        



class DeleteDownloadedFileRequest(BaseModel):
    file_path: str
    project_name: str

    

class UndoFileRequest(BaseModel):
    file_path: str    
    project_name: str



class ViewContentRequest(BaseModel):
    file_path: str   
    project_name: str 