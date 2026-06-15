

import os, time, requests, re, httpx, logging, uuid
from fastapi import Request, HTTPException
from schemas.semantic_scholar_schemas import SemanticScholarRetriverRequest
from core.utils import utility
from core.utils.gcp_utils import upload_text_file, upload_pdf_from_path
from services.search_services import add_search_term
from database.database import get_db
import traceback
from requests.exceptions import ConnectTimeout, ReadTimeout
from datetime import datetime


logger = logging.getLogger("semantic_scholar")
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(request_id)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")


_last_request_time = 0.0
_RATE_LIMIT_DELAY = 1.0  

def _log_context(request_id: str):
    return {"request_id": request_id}




async def retrive_semantic_scholar(request: Request, data: SemanticScholarRetriverRequest):
    request_id = str(uuid.uuid4())[:8]
    ctx = _log_context(request_id)
    logger.info("retrive_semantic_scholar START", extra=ctx)

    user_id = request.state.user.get("user_id")
    logger.debug(f"user_id={user_id} project={data.project_name}", extra=ctx)

    query = utility.construct_query(
        data.search_terms,
        data.operators,
        data.country,
        data.patient_cohort
    )
    logger.info(f"constructed query: {query!r}", extra=ctx)

    add_search_result = add_search_term(user_id=user_id, term=query, db=next(get_db()))
    if not add_search_result:
        logger.error("failed to log search term in DB", extra=ctx)
        raise HTTPException(status_code=500, detail="Something is not working. Please try again!")

    topic = sanitize_filename(query.replace(' ', '_'))
    dir_ = f"users/{user_id}/{data.project_name}/semantic_scholar/{topic}"
    logger.debug(f"output directory: {dir_}", extra=ctx)

    try:
        num_success, num_failed = await main(query, data.max_pdfs, output_dir=dir_)

        return {
            "success": num_success,
            "failed": num_failed,
            "downloaded": num_success,
            "skipped_403": 0,
            "failed_downloads": num_failed,
            "source": "semantic_scholar"
        }

    except Exception as e:
        logger.exception("unexpected error in retrive_semantic_scholar", extra=ctx)
        return {
            "success": 0,
            "failed": data.max_pdfs,
            "downloaded": 0,
            "skipped_403": 0,
            "failed_downloads": data.max_pdfs,
            "error": str(e),
            "source": "semantic_scholar"
        }




async def main(keyword, max_results, output_dir):
    ctx = _log_context(getattr(logging.getLogger(), "request_id", "UNKNOWN"))
    logger.info(f"main START – keyword={keyword!r} max_results={max_results}", extra=ctx)

    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"ensured output_dir: {output_dir}", extra=ctx)

        all_pdf_links = []
        all_metadata = []
        seen_urls = set()

        # 1. With API key
        if SEMANTIC_SCHOLAR_API_KEY:
            logger.info("Searching with API key (higher limits)", extra=ctx)
            links1, meta1 = get_pdf_links(keyword, max_results, use_api_key=True)
            for link, meta in zip(links1, meta1):
                if link not in seen_urls:
                    seen_urls.add(link)
                    all_pdf_links.append(link)
                    all_metadata.append({**meta, "source": "api_key"})
            logger.info(f"PDFs received from API (with key): {len(links1)}", extra=ctx)
        else:
            logger.info("No API key found – skipping authenticated search", extra=ctx)

        # 2. Without API key (public)
        logger.info("Searching public API (no key)", extra=ctx)
        links2, meta2 = get_pdf_links(keyword, max_results, use_api_key=False)
        new_added = 0
        for link, meta in zip(links2, meta2):
            if link not in seen_urls:
                seen_urls.add(link)
                all_pdf_links.append(link)
                all_metadata.append({**meta, "source": "public"})
                new_added += 1
        logger.info(f"PDFs received from public API (no key): {len(links2)} (added {new_added} new)", extra=ctx)

        
        all_pdf_links = all_pdf_links[:max_results]
        all_metadata = all_metadata[:max_results]

        if not all_pdf_links:
            logger.warning("No PDF links found from either source", extra=ctx)
            raise ValueError("No PDF links found in the search results")

        logger.info(f"TOTAL unique PDFs to download: {len(all_pdf_links)}", extra=ctx)

        num_success, num_failed = await download_pdfs(all_pdf_links, all_metadata, output_dir)
        logger.info(f"main END – success:{num_success} failed:{num_failed}", extra=ctx)
        return num_success, num_failed

    except Exception as e:
        logger.exception("unexpected error in main", extra=ctx)
        return 0, max_results





def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename).strip()





def get_pdf_links(keyword, max_results, use_api_key: bool):
    ctx = _log_context(getattr(logging.getLogger(), "request_id", "UNKNOWN"))
    mode = "with API key" if use_api_key else "public"
    logger.debug(f"get_pdf_links START [{mode}] – keyword={keyword!r} max={max_results}", extra=ctx)

    pdf_links, metadatas = [], []
    offset = 0
    while len(pdf_links) < max_results:
        logger.debug(f"[{mode}] fetching page offset={offset}", extra=ctx)
        data = search_semantic_scholar(keyword, offset, limit=10, use_api_key=use_api_key)
        new_links, new_meta = extract_pdf_links(data)

        pdf_links.extend(new_links)
        metadatas.extend(new_meta)

        pdf_links = pdf_links[:max_results]
        metadatas = metadatas[:max_results]

        if not new_links:
            logger.info(f"[{mode}] no more results – stopping", extra=ctx)
            break
        offset += 10

    logger.debug(f"get_pdf_links END [{mode}] – found {len(pdf_links)}", extra=ctx)
    return pdf_links, metadatas





def _enforce_rate_limit():
    """Ensure at least 1 second between any two API calls."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _RATE_LIMIT_DELAY:
        sleep_time = _RATE_LIMIT_DELAY - elapsed
        logger.debug(f"Rate-limit sleep: {sleep_time:.2f}s")
        time.sleep(sleep_time)
    _last_request_time = time.time()





def search_semantic_scholar(keyword, offset=0, limit=10, use_api_key: bool = False):
    ctx = _log_context(getattr(logging.getLogger(), "request_id", "UNKNOWN"))
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": keyword, "offset": offset, "limit": limit,
        "fields": "paperId,title,authors,year,abstract,url,openAccessPdf,publicationVenue"
    }
    headers = {}
    if use_api_key:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY

    max_retries = 3
    for attempt in range(max_retries):
        _enforce_rate_limit()  # 1 request / second

        logger.debug(f"calling SemanticScholar API [{'(auth)' if use_api_key else ''}] – attempt {attempt+1}/{max_retries}", extra=ctx)
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code == 429:
                wait = 2 ** attempt  # 1, 2, 4 seconds
                logger.warning(f"Rate limit (429) – retrying in {wait}s (attempt {attempt+1})", extra=ctx)
                time.sleep(wait)
                continue
            response.raise_for_status()
            data = response.json()
            count = len(data.get("data", []))
            logger.debug(f"API response OK – {count} items", extra=ctx)
            return data
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in (401, 403):
                logger.error(f"Auth error {e.response.status_code}: {'Invalid key' if e.response.status_code == 401 else 'Forbidden'}", extra=ctx)
                break
            logger.error(f"search_semantic_scholar HTTP error: {e}", extra=ctx)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            break
        except Exception as e:
            logger.error(f"search_semantic_scholar error: {e}", extra=ctx)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            break
    return {"data": []}





def extract_pdf_links(data):
    ctx = _log_context(getattr(logging.getLogger(), "request_id", "UNKNOWN"))
    links, metadata = [], []

    for result in data.get("data", []):
        if result.get("openAccessPdf"):
            pdf_url = result["openAccessPdf"].get("url")
            if pdf_url:
                links.append(pdf_url)
                d = {
                    'title': result.get('title', 'Unknown'),
                    'source': result.get('url', ''),
                    'authors': [a.get('name', '') for a in result.get('authors', [])],
                    'year': result.get('year'),
                    'url': pdf_url,
                    'abstract': result.get('abstract', '')
                }
                metadata.append(d)
    logger.debug(f"extracted {len(links)} PDF links from page", extra=ctx)
    return links, metadata






async def download_pdfs(pdf_links, metadatas: list[dict], output_dir):
    ctx = _log_context(getattr(logging.getLogger(), "request_id", "UNKNOWN"))
    logger.info(f"download_pdfs START – {len(pdf_links)} PDFs", extra=ctx)

    num_success, num_failed = 0, 0
    for ind, link in enumerate(pdf_links, start=1):
        metadata = metadatas[ind - 1]
        source = metadata.get("source", "unknown")
        ok = download_pdf_with_status(link, metadata, output_dir, ind, source_label=source)
        if ok:
            num_success += 1
        else:
            num_failed += 1

    logger.info(f"download_pdfs END – success:{num_success} failed:{num_failed}", extra=ctx)
    return num_success, num_failed





def download_pdf_with_status(link, metadata, output_dir, ind, source_label):
    ctx = _log_context(getattr(logging.getLogger(), "request_id", "UNKNOWN"))
    logger.debug(f"downloading PDF #{ind} [{source_label}] – {link}", extra=ctx)

    try:
        download(link, metadata, output_dir, ind)
        logger.debug(f"PDF #{ind} downloaded & uploaded [{source_label}]", extra=ctx)
        return True
    except Exception as e:
        logger.error(f"PDF #{ind} FAILED [{source_label}] – {str(e)}", extra=ctx)
        return False   






def download(url, metadata: dict, dir_, ind):
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/pdf'}
    file_path = None
    ctx = _log_context(getattr(logging.getLogger(), "request_id", "UNKNOWN"))
    dir_ = dir_.replace("\\", "/").rstrip("/") + "/"
    base_name = os.path.basename(dir_.rstrip("/"))

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=60)
            
            if response.status_code == 403:
                logger.info(f"PDF #{ind} blocked by publisher (403) – skipping", extra=ctx)
                raise RuntimeError("Access forbidden (403)")

            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}")

            filename_base = f"{base_name}_{ind}"
            txt_filename = f"{filename_base}.txt"
            pdf_filename = f"{filename_base}.pdf"


            txt_key = f"{dir_}/{txt_filename}".replace("//", "/")
            pdf_path_local = os.path.join(dir_, pdf_filename)

            
            txt_content = f"""Title: {metadata.get('title', 'Unknown')}
Authors: {', '.join(metadata.get('authors', ['Unknown']))}
Year: {metadata.get('year') or 'Unknown'}
Source: {metadata.get('source', 'Unknown')}
URL: {metadata.get('url', 'Unknown')}
Fetched Date: {datetime.now().strftime('%b %d, %Y at %H:%M')}
Fetched From: semantic_scholar
"""

            upload_text_file(path=txt_key, file=txt_content)
            logger.debug(f"Metadata uploaded: {txt_key}")

            
            with open(pdf_path_local, "wb") as f:
                f.write(response.content)

            upload_pdf_from_path(pdf_path_local)
            logger.debug(f"PDF uploaded: {pdf_path_local}")
            return True

        except (ConnectTimeout, ReadTimeout) as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.warning(f"Timeout on PDF #{ind}, retry {attempt+1}/{max_retries} in {wait}s", extra=ctx)
                time.sleep(wait)
                continue
            raise
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise  
        
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Local file removed: {file_path}")
                except:
                    pass

    raise RuntimeError("Download failed after retries")