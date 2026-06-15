
import os
import re
from core.utils.gcp_utils import list_files_in_folder, download_text_file
from fastapi import HTTPException
from datetime import datetime
import os
import re
import logging


async def list_downloaded_articles_with_dates(user_id: str, project_name: str):
    base_prefix = f"users/{user_id}/{project_name}/"
    files = []

    sources = ["google_scholar", "semantic_scholar", "pubmed"]

    for source in sources:
        source_prefix = f"{base_prefix}{source}/"
        try:
            
            all_blobs = await list_files_in_folder(source_prefix)
        except Exception as e:
            logging.warning(f"Failed to list {source_prefix}: {e}")
            continue

        for blob_name in all_blobs:
            if not blob_name.endswith(".pdf"):
                continue

            
            txt_path = blob_name.replace(".pdf", ".txt")
            relative_path = blob_name[len(base_prefix):]  

            
            try:
                txt_content = await download_text_file(txt_path)
                meta = parse_metadata_txt(txt_content)
            except HTTPException as e:
                if e.status_code == 404:
                    meta = {"title": "Unknown", "year": "Unknown", "fetch_date": "Unknown", "authors": "Unknown"}
                else:
                    meta = {"title": "Unknown", "year": "Unknown", "fetch_date": "Unknown", "authors": "Unknown"}

            
            clean_title = os.path.basename(blob_name)
            if clean_title.endswith(".pdf"):
                clean_title = clean_title[:-4]  
            clean_title = clean_title.replace("_", " ").strip()

            files.append({
                "title": meta.get("title", "Untitled Paper") or clean_title,
                "filename": os.path.basename(blob_name),
                "relative_path": relative_path,
                "full_path": blob_name,
                "source": meta.get("fetched_from", source.replace("_", " ").title().replace("Scholer", "Scholar")),
                "fetch_date": meta.get("fetch_date", "Unknown"),
                "year": meta.get("year", "Unknown"),
                "authors": meta.get("authors", "Unknown")
            })

    
    files.sort(key=lambda x: x["fetch_date"] if x["fetch_date"] != "Unknown" else "1900-01-01", reverse=True)
    return files





def parse_metadata_txt(content: str) -> dict:
    data = {
        "title": "Unknown",
        "authors": "Unknown",
        "year": "Unknown",
        "fetch_date": "Unknown",
        "fetched_from": "Unknown"
    }

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    
    current_date = datetime.now().strftime("%b %d, %Y")

    for line in lines:
        if ": " in line:
            key_part, value = line.split(": ", 1)
        elif ":" in line:
            key_part, value = line.split(":", 1)
        else:
            continue

        key = key_part.strip().lower()
        value = value.strip()

        if key in ["title"]:
            data["title"] = value or "Unknown"
        elif key in ["authors", "author"]:
            data["authors"] = value or "Unknown"
        elif key in ["journal", "fulljournalname"]:
            if data["title"] == "Unknown":
                data["title"] = value
        elif key in ["date", "pubdate", "publication date"]:
            year_match = re.search(r'\b(19|20)\d{2}\b', value)
            if year_match:
                data["year"] = year_match.group(0)
            else:
                data["year"] = "N/A"
        elif key in ["pmcid", "pmid"]:
            
            pass
        
        if "fetched_from" not in data or data["fetched_from"] == "Unknown":
            if "PMC" in value or key == "pmcid":
                data["fetched_from"] = "PubMed Central"

    
    if data["title"] == "Unknown":
        data["title"] = "Untitled PubMed Article"

    
    if data["fetch_date"] == "Unknown":
        data["fetch_date"] = current_date.split(",")[0]  

    
    if data["fetched_from"] == "Unknown":
        data["fetched_from"] = "PubMed"

    return data