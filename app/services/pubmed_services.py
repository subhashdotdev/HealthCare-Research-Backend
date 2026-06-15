import time
import re
import os
import logging
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from core.utils.gcp_utils import upload_pdf_from_path, upload_text_file,upload_pdf_from_bytes
from services.search_services import add_search_term
from database.database import get_db
from schemas.pubmed_schemas import PubmedRetriverRequest
from core.utils import utility
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()



# ==================== CONFIG ====================
NCBI_API_KEY = os.getenv("PUBMED_NCBI_API_KEY")  

# E-utilities base URLs
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# Direct PDF download 
PDF_BASE_URL = "https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmcid}&blobtype=pdf"


REQUEST_DELAY = 0.11  

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"




def gcp_path(path: str) -> str:
    return path.replace("\\", "/")




def retrive_pubmed(request: Request, data: PubmedRetriverRequest):
    user_id = request.state.user.get("user_id")
    project_name = data.project_name
    country = data.country
    patient_cohort = data.patient_cohort
    terms = data.search_terms
    operators = data.operators
    max_pdfs = data.max_pdfs

    query = utility.construct_query(terms, operators, country, patient_cohort)

  
    add_search_result = add_search_term(user_id=user_id, term=query, db=next(get_db()))
    if not add_search_result:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Failed to save search term."}
        )

    topic = query.replace(' ', '_').replace('"', '')
    output_dir = f"users/{user_id}/{project_name}/pubmed/{topic}"
    os.makedirs(output_dir, exist_ok=True)

    try:
        success, failed = main(query, max_pdfs, output_dir)

        return {
            "success": success,
            "failed": failed,
            "downloaded": success,       
            "skipped_403": 0,             
            "failed_downloads": failed, 
            "source": "pubmed"           
        }

    except Exception as e:
        logging.exception("Error in PubMed retrieval")
        return {
            "success": 0,
            "failed": 0,
            "downloaded": 0,
            "skipped_403": 0,
            "failed_downloads": 0,
            "source": "pubmed",
            "error": str(e)
        }






def main(keyword: str, max_pdfs: int, output_dir: str) -> Tuple[int, int]:
    print(f"Searching PubMed Central for: {keyword}")
    print(f"Saving PDFs to: {output_dir}")

    start_time = time.time()

    
    pmcids = get_pmcids_via_eutils(keyword, max_pdfs)
    print(f"Found {len(pmcids)} open-access PMC articles")

    if not pmcids:
        return 0, max_pdfs

    
    success, failed = download_pdfs_parallel(pmcids, output_dir)

    elapsed = time.time() - start_time
    print(f"Done in {elapsed:.1f}s → {success} downloaded, {failed} failed")
    return success, failed


def get_pmcids_via_eutils(keyword: str, max_results: int) -> List[str]:
    """Use NCBI ESearch to get PMCIDs (open access only)"""
    pmcids = []

    params = {
        "db": "pmc",
        "term": keyword,
        "retmax": max_results,
        "retmode": "xml",
        "rettype": "uilist",
        "sort": "relevance"
    }
    if NCBI_API_KEY and NCBI_API_KEY != "YOUR_NCBI_API_KEY_HERE":
        params["api_key"] = NCBI_API_KEY

    try:
        response = requests.get(ESEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        for id_elem in root.findall(".//Id"):
            pmcid = f"PMC{id_elem.text}"
            pmcids.append(pmcid)

        time.sleep(REQUEST_DELAY)
    except Exception as e:
        logging.error(f"ESearch failed: {e}")

    return pmcids[:max_results]





def get_article_metadata(pmcid: str) -> dict:
    """Fetch title, authors, journal, etc. using ESummary"""
    pmcid_num = pmcid.replace("PMC", "")
    params = {
        "db": "pmc",
        "id": pmcid_num,
        "retmode": "xml"
    }
    if NCBI_API_KEY and NCBI_API_KEY != "YOUR_NCBI_API_KEY_HERE":
        params["api_key"] = NCBI_API_KEY

    try:
        response = requests.get(ESUMMARY_URL, params=params, timeout=20)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        doc = root.find(".//DocumentSummary")
        if not doc:
            return {"Title": "Unknown", "Authors": "", "Journal": "", "Date": ""}

        title = doc.findtext("Title", "Unknown Title")
        authors = ", ".join([a.findtext("Name", "") for a in doc.findall(".//Author")])
        journal = doc.findtext("FullJournalName", "Unknown Journal")
        pubdate = doc.findtext("PubDate", "")[:10]

        time.sleep(REQUEST_DELAY)
        return {
            "Title": title,
            "Authors": authors or "Unknown Authors",
            "Journal": journal,
            "Date": pubdate,
            "PMCID": pmcid
        }
    except Exception as e:
        logging.warning(f"Metadata failed for {pmcid}: {e}")
        return {"Title": pmcid, "Authors": "Unknown", "Journal": "Unknown", "Date": ""}







def download_pdf(pmcid: str, output_dir: str, index: int) -> bool:
    folder_name = Path(output_dir).name
    pdf_filename = f"{folder_name}_{index + 1}.pdf"
    txt_filename = f"{folder_name}_{index + 1}.txt"

    local_pdf_path = Path(output_dir) / pdf_filename
    local_txt_path = Path(output_dir) / txt_filename

    gcp_pdf_path = gcp_path(f"{output_dir}/{pdf_filename}")
    gcp_txt_path = gcp_path(f"{output_dir}/{txt_filename}")

    if local_pdf_path.exists() and local_pdf_path.stat().st_size > 50000:
        return True

    try:
        response = requests.get(
            PDF_BASE_URL.format(pmcid=pmcid),
            headers={"User-Agent": USER_AGENT, "Referer": "https://europepmc.org/"},
            timeout=60
        )
        response.raise_for_status()

        pdf_bytes = response.content
        if len(pdf_bytes) < 10000:
            logging.warning(f"{pmcid}: File too small, likely not a PDF")
            return False

        
        local_pdf_path.write_bytes(pdf_bytes)

        
        upload_pdf_from_bytes(gcp_pdf_path, pdf_bytes)  
        logging.info(f"[GCP] PDF uploaded: {gcp_pdf_path}")

        
        metadata = get_article_metadata(pmcid)
        current_date = datetime.now().strftime("%b %d, %Y at %H:%M")

        metadata_text = f"""Title: {metadata.get("Title", "Unknown Title")}
        Authors: {metadata.get("Authors", "Unknown Authors")}
        Journal: {metadata.get("Journal", "Unknown Journal")}
        Date: {metadata.get("Date", "Unknown")}
        PMCID: {pmcid}
        Fetched From: PubMed Central
        Fetch Date: {current_date}
        """

        local_txt_path.write_text(metadata_text, encoding="utf-8")
        upload_text_file(gcp_txt_path, metadata_text)
        logging.info(f"[GCP] Metadata uploaded: {gcp_txt_path}")

        return True

    except Exception as e:
        logging.error(f"Failed {pmcid}: {e}")
        if local_pdf_path.exists():
            local_pdf_path.unlink(missing_ok=True)
        return False

    finally:
        time.sleep(REQUEST_DELAY)





def download_pdfs_parallel(pmcids: List[str], output_dir: str) -> Tuple[int, int]:
    success = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(download_pdf, pmcid, output_dir, i): pmcid
            for i, pmcid in enumerate(pmcids)
        }

        for future in as_completed(futures):
            result = future.result()
            if result:
                success += 1
            else:
                failed += 1

    return success, failed




