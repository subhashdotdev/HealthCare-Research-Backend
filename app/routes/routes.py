from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Request, Depends, status, Request
from fastapi.responses import JSONResponse
from typing import Optional
from database.database import get_db
from sqlalchemy.orm import Session
from fastapi import FastAPI, Request
from pydantic import BaseModel
import uuid
import logging


#================================ Schemas ===============================================#
from schemas.pubmed_schemas import PubmedRetriverRequest
from schemas.google_scholer_schemas import GoogleScholerRetriverRequest
from schemas.semantic_scholar_schemas import SemanticScholarRetriverRequest # Semantic Scholar API
from schemas.extractors_schemas import TermExtractorRequest
from schemas.project_schemas import CreateNewProjectRequest, DownloadArticles, SummarizeRequest,MainFindingsRequest, ProjectListResponse, DeleteProjectRequest
from schemas.common_words_analysis_schemas import GetAllFoldersRequest, ExtractCommonWordsRequest, DownloadCWAPdfRequest
from schemas.filter_schemas import ExcludeFileRequest, ExcludeFileResponse, IncludeFileRequest, IncludeFileResponse, DeleteDownloadedFileRequest, UndoFileRequest, ViewContentRequest
from schemas.search_schemas import DeleteRecentSearchRequest
#============================== Services ================================================#
from services.file_listing_service import list_downloaded_articles_with_dates
from services.pubmed_services import retrive_pubmed
from services.summarizepdf import summarize_pdf,main_findings_pdf
from services.google_scholer_services import retrive_google_scholer
from services.term_extractor_services import term_extractor
from services.table_extractor_services import extract_tables
from services.image_extractor_services import extract_images
from services.combined_extractor_services import extract_table_and_image
from services.aws_services import create_new_project, existing_project_list, download_article, delete_project
from services.common_words_analysis import get_all_project_data, common_words_analysis, download_cwa_pdf_from_source
from services.search_services import user_recent_searches, delete_specific_recent_search
from services.filter_services import exclude_specific_file, include_specific_file, delete_downloaded_file, undo_specific_file, view_file_content
from services.semantic_scholar_services import retrive_semantic_scholar # Semantic Scholar API
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from services.chat_pdf import chat_with_pdf_timed, start_chat_session_resilient,end_chat_session_timed
from core.jwt import verify_token




router = APIRouter()



@router.post("/create_new_project")
async def create_project(request: Request, data:CreateNewProjectRequest):
     return create_new_project(request=request, data=data)




@router.post("/get_existing_projects", response_model=ProjectListResponse)
async def get_existing_projects(request: Request):
    projects = existing_project_list(request=request)
    return {"projects": projects}



@router.post("/retrive_pubmed_article")
async def retrive_pubmed_articles(request: Request, data: PubmedRetriverRequest):
    return retrive_pubmed(request = request, data = data)



@router.post("/retrive_google_scholer_article")
async def retrive_google_scholer_articles(request: Request, data: GoogleScholerRetriverRequest):
    return await retrive_google_scholer(request = request ,data = data)






@router.post("/retrive_semantic_scholar_article")
async def retrive_semantic_scholar_articles(request: Request, data: SemanticScholarRetriverRequest):
    request_id = str(uuid.uuid4())[:8]
    logger = logging.getLogger("semantic_scholar")
    logger_adapter = logging.LoggerAdapter(logger, {"request_id": request_id})
    return await retrive_semantic_scholar(request=request, data=data)




@router.post("/term_extractor")
async def extract_term( article_type: str = Form(...),  
    surgical_device_name: Optional[str] = Form(None), 
    surgical_technique: Optional[str] = Form(None),
    diagnostic_test_type: Optional[str] = Form(None),
    diagnostic_test_name: Optional[str] = Form(None),
    diagnostic_sample_type: Optional[str] = Form(None),
    diagnostic_technique: Optional[str] = Form(None),
    file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File type must be PDF.")
    
    return term_extractor(article_type,
                          surgical_device_name,
                          surgical_technique,
                          diagnostic_test_type,
                          diagnostic_test_name,
                          diagnostic_sample_type,
                          diagnostic_technique,
                          file)




@router.post("/table_extractor")
async def extract_table(request:Request, project_name:str = Form(...), file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File type must be PDF.")
    return await extract_tables(request,project_name, file)




@router.post("/image_extractor")
async def extract_image(request: Request, project_name:str = Form(...), file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File type must be PDF.")
    return await extract_images(request,project_name, file)




@router.post("/combined_extractor")
async def extract_tables_and_images(request: Request, project_name:str = Form(...), file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File type must be PDF.")
    return await extract_table_and_image(request,project_name,file)




@router.post("/get_all_file_and_folders")
async def cwa_get_all_files_and_folders(request:Request, data:GetAllFoldersRequest):
    return get_all_project_data(request=request, data =data)





@router.post("/extract_common_words")
async def extract_common_words(request:Request,data:ExtractCommonWordsRequest):
    return common_words_analysis(request=request, data=data)



@router.post("/download_cwa_pdf")
async def download_cwa_pdf(request:Request,data:DownloadCWAPdfRequest):
    return await download_cwa_pdf_from_source(request=request, data=data)



@router.post("/download_articles")
async def download_articles(request:Request, data:DownloadArticles):
    return download_article(request=request, data=data)




@router.get("/recent_searches")
async def recent_searches(request:Request, db: Session = Depends(get_db)):
    return await user_recent_searches(request=request, db=db)




@router.post("/delete_recent_search")
async def delete_recent_search(data:DeleteRecentSearchRequest, db:Session = Depends(get_db)):
    return delete_specific_recent_search(data=data, db=db)




@router.post("/exclude_file", response_model = ExcludeFileResponse)
async def exclude_file(request: Request, data: ExcludeFileRequest):
    return exclude_specific_file(request=request, data=data)




@router.post("/include_file", response_model=IncludeFileResponse)
async def include_file(request: Request, data: IncludeFileRequest):
    return include_specific_file(request=request, data=data)




@router.post("/retrive_scholar_and_pubmed_articles")
async def retrive_scholar_and_pubmed_articles(request: Request, data: GoogleScholerRetriverRequest):

    number = data.max_pdfs
    if number <= 0:
        raise HTTPException(status_code=422, detail="Number of downloads must be greater than 0.")

    # Split PDFs download count
    half = number // 2

    # --- GOOGLE SCHOLAR ---
    data.max_pdfs = half + (1 if number % 2 != 0 else 0)
    scholar_result = await retrive_google_scholer(request=request, data=data)

    # --- PUBMED ---
    data.max_pdfs = half
    pubmed_result = retrive_pubmed(request=request, data=data)

   
    final_result = {
        "success": scholar_result["success"] + pubmed_result["success"],
        "failed": scholar_result["failed"] + pubmed_result["failed"],
        "downloaded": scholar_result["downloaded"] + pubmed_result["downloaded"],
        "skipped_403": scholar_result.get("skipped_403", 0) + pubmed_result.get("skipped_403", 0),
        "failed_downloads": scholar_result["failed_downloads"] + pubmed_result["failed_downloads"],
        "source": "google_scholar + pubmed"
    }

    return final_result





@router.post("/retrive_scholar_and_semantic")
async def retrive_scholar_and_semantic(request: Request, data: GoogleScholerRetriverRequest):

    number = data.max_pdfs
    if number <= 0:
        raise HTTPException(status_code=422, detail="Number of downloads should be greater than 0.")

    # Split PDFs
    half = number // 2

    # --- GOOGLE SCHOLAR ---
    data.max_pdfs = half
    google_result = await retrive_google_scholer(request=request, data=data)

    # --- SEMANTIC SCHOLAR ---
    remaining = number - half
    data.max_pdfs = remaining
    semantic_result = await retrive_semantic_scholar(request=request, data=data)

    # --- MERGE INTO FINAL FLAT RESULT ---
    final_result = {
        "success": google_result["success"] + semantic_result["success"],
        "failed": google_result["failed"] + semantic_result["failed"],
        "downloaded": google_result["downloaded"] + semantic_result["downloaded"],
        "skipped_403": google_result["skipped_403"] + semantic_result["skipped_403"],
        "failed_downloads": google_result["failed_downloads"] + semantic_result["failed_downloads"],
        "source": "google_scholar + semantic_scholar"
    }

    return final_result



@router.post("/delete_file")
async def delete_file_endpoint(request: Request, data: DeleteDownloadedFileRequest):
    return delete_downloaded_file(request=request, data=data)  




@router.post("/undo_file")
async def undo_file_endpoint(data: UndoFileRequest, request: Request):
    return undo_specific_file(data=data, request=request)





@router.post("/view_content")
async def content_view(
    data: ViewContentRequest,
    request: Request   
):
    return await view_file_content(data=data, request=request)





@router.post("/summarize_pdf")
async def summarize_pdf_endpoint(request: Request, data: SummarizeRequest):
    return await summarize_pdf(request=request, data=data)




@router.post("/main_findings_pdf")
async def main_findings_pdf_endpoint(request: Request, data: MainFindingsRequest):
    return await main_findings_pdf(request=request, data=data)




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token")


class SessionRequest(BaseModel):
    project_name: str
    relative_path: str



def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload["user_id"]



@router.post("/start_chat_session")
async def start_session(
    request: SessionRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    full_path = f"users/{user_id}/{request.project_name}/{request.relative_path}"
    print(f"[CHAT] Full path: {full_path}")
    
    return await start_chat_session_resilient(full_path, db)




class ChatRequest(BaseModel):
    session_id: str
    project_name: str
    relative_path: str
    query: str


@router.post("/chat_with_pdf")
async def chat(request: ChatRequest, user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    full_path = f"users/{user_id}/{request.project_name}/{request.relative_path}"
    return await chat_with_pdf_timed(request.session_id, full_path, request.query, db)
    



class EndSessionRequest(BaseModel):
    session_id: str


@router.post("/end_chat_session")
async def end_session(request: EndSessionRequest, user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    return await end_chat_session_timed(request.session_id, user_id, db)
    


@router.post("/list_downloaded_articles")
async def get_downloaded_articles(request: Request, project_name: str = Form(...)):
    user_id = request.state.user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    files = await list_downloaded_articles_with_dates(user_id, project_name)
    return {"files": files}




@router.post("/delete_project")
async def delete_project_endpoint(request: Request,data: DeleteProjectRequest):
    return delete_project(request=request, project_name=data.project_name)
   





