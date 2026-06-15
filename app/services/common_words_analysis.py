from fastapi import Request, UploadFile, HTTPException
from core.utils.aws_utils import s3_get_folders, s3_get_all_files
from schemas.common_words_analysis_schemas import GetAllFoldersRequest, ExtractCommonWordsRequest, DownloadCWAPdfRequest
from core.utils.pdf_utils import process_pdfs
from services.analysis_services import run_openai_finding_keywords_for_search
from core.utils.string_utils import string_to_python_list
import services.pubmed_services as pubmed
import services.google_scholer_services as google
from core.utils.gcp_utils import get_all_files_and_folders_in_project
import re




def get_all_project_data(request:Request, data:GetAllFoldersRequest):
    user_id = request.state.user.get("user_id")
    project_name = data.project_name
    path = f"users/{user_id}/{project_name}"
    return get_all_files_and_folders_in_project(path=path)





def common_words_analysis(request: Request, data: ExtractCommonWordsRequest):
    user_id = request.state.user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    project_name = data.project_name
    relative_path = data.s3_pdf_path.strip("/")

    
    full_s3_path = f"users/{user_id}/{project_name}/{relative_path}"
    print(f"[CWA] Full S3 path: {full_s3_path}")

    try:
        results = process_pdfs(full_s3_path)  
        if not results:
            raise HTTPException(status_code=404, detail="No text extracted from PDF or file not readable.")

        raw_output = run_openai_finding_keywords_for_search(results)
        common_words = string_to_python_list(raw_output)
        return {"common_words": common_words}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found.")
    except Exception as e:
        print(f"Error in common_words_analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to process PDF")
    




async def download_cwa_pdf_from_source(request:Request, data:DownloadCWAPdfRequest):
    user_id = request.state.user.get("user_id")
    term = data.download_term
    source = data.download_source
    project_name = data.project_name
    print("TERM:", term)
    print("SOURCE:", source)
    print("PROJECT NAME:", project_name)
    topic = sanitize_filename(term.replace(' ', '_'))
    pub_dir = f"users/{user_id}/{project_name}/pubmed/{topic}"
    scholer_dir = f"users/{user_id}/{project_name}/google_scholer/{topic}"
    print("DIR_PATH", scholer_dir)
    if source == "PUBMED":
        print("PUBMED")
        return pubmed.main(term, 20, pub_dir)
    else:
        print("GGOLE SCHOILAR")
        return await google.main(term, 20, scholer_dir)
    
    
    

def sanitize_filename(filename):
    """
    Replace invalid characters in filenames or paths to make them safe for use on Windows.
    """
    return re.sub(r'[<>:"/\\|?*]', '', filename).strip()