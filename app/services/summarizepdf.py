
import fitz
from openai import OpenAI
from fastapi import HTTPException, Request
from core.utils.gcp_utils import bucket
from schemas.project_schemas import SummarizeRequest,MainFindingsRequest
import re





def _clean_path(path: str) -> str:
    """Convert \\ → / and normalize"""
    return re.sub(r'\\+', '/', path).strip('/')





async def summarize_pdf(request: Request, data: SummarizeRequest):
    user_id = request.state.user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    project_name = data.project_name
    relative_path = _clean_path(data.path)  

    full_gcs_path = f"users/{user_id}/{project_name}/{relative_path}"
    print(f"[SUMMARIZE] GCS Path: {full_gcs_path}")

    try:
        blob = bucket.get_blob(full_gcs_path)
        if not blob:
            raise HTTPException(status_code=404, detail="PDF not found in bucket")

        pdf_bytes = blob.download_as_bytes()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = doc.page_count
        text = ""
        extracted_pages = 0

        for page_num in range(min(5, page_count)):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            if page_text.strip():
                text += page_text + "\n"
                extracted_pages += 1

        doc.close()  

        if not text.strip():
            return {
                "status": "warning",
                "summary": "No extractable text found. PDF may be scanned or image-based.",
                "path": relative_path
            }
        client = OpenAI()
        prompt = f"Summarize this research paper in 150–200 words:\n\n{text[:12000]}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in summarizing medical and scientific research papers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.5
        )

        summary = response.choices[0].message.content.strip()

        return {
            "status": "success",
            "summary": summary,
            "path": relative_path,
            "extracted_pages": extracted_pages
        }

    except Exception as e:
        print(f"[SUMMARIZE ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")






async def main_findings_pdf(request: Request, data: MainFindingsRequest):
    user_id = request.state.user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    project_name = data.project_name
    relative_path = _clean_path(data.path)

    full_gcs_path = f"users/{user_id}/{project_name}/{relative_path}"

    try:
        blob = bucket.get_blob(full_gcs_path)
        if not blob:
            raise HTTPException(status_code=404, detail="PDF not found")

        pdf_bytes = blob.download_as_bytes()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = doc.page_count
        text = ""
        extracted_pages = 0

        for page_num in range(min(5, page_count)):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            if page_text.strip():
                text += page_text + "\n"
                extracted_pages += 1

        doc.close()

        if not text.strip():
            return {"status": "warning", "main_findings": "No text extracted.", "path": relative_path}

        client = OpenAI()
        prompt = f"Extract the main findings in 3–5 bullet points:\n\n{text[:15000]}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a medical researcher extracting key findings."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )

        findings = response.choices[0].message.content.strip()

        return {
            "status": "success",
            "main_findings": findings,
            "path": relative_path,
            "extracted_pages": extracted_pages
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract findings: {str(e)}")
