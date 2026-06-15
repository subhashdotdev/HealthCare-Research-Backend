from typing import List
from pydantic import BaseModel




class CreateNewProjectRequest(BaseModel):
    project_name:str
    project_description:str



class DownloadArticles(BaseModel):
    project_name:str
    path: str    



class ProjectListResponse(BaseModel):
    projects: List[str]




class DeleteProjectRequest(BaseModel):
    project_name: str



class SummarizeRequest(BaseModel):
    project_name: str
    path: str



class MainFindingsRequest(BaseModel):
    project_name: str
    path: str