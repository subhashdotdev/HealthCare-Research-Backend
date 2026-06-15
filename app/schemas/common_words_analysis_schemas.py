from pydantic import BaseModel



class GetAllFoldersRequest(BaseModel):
    project_name:str



class ExtractCommonWordsRequest(BaseModel):
    project_name: str
    s3_pdf_path: str



class DownloadCWAPdfRequest(BaseModel):
    download_term: str
    download_source: str
    project_name: str



class CommonWordsAnalysisRequest(BaseModel):
    data_source: str
    