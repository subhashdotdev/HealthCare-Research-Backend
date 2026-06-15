
import os, time, requests, re, httpx, logging, traceback
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from core import settings
from schemas.google_scholer_schemas import GoogleScholerRetriverRequest
from core.utils import utility
from core.utils.gcp_utils import upload_text_file, upload_pdf_from_path
from services.search_services import add_search_term
from database.database import get_db
from datetime import datetime


load_dotenv(override=True)


logger = logging.getLogger("google_scholar")
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)





async def retrive_google_scholer(request: Request, data: GoogleScholerRetriverRequest):
    user_id = request.state.user.get("user_id")
    project_name = data.project_name
    query = utility.construct_query(data.search_terms, data.operators, data.country, data.patient_cohort)

    if not add_search_term(user_id=user_id, term=query, db=next(get_db())):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Something is not working. Please try again!"}
        )

    topic = sanitize_filename(query.replace(' ', '_'))
    dir_ = f"users/{user_id}/{project_name}/google_scholar/{topic}"

    try:
        result = await main(query, data.max_pdfs, output_dir=dir_)
        result["source"] = "google_scholar"
        return result
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()
        return {"error": str(e), "source": "google_scholar"}




async def main(keyword, max_results, output_dir):
    output_dir = output_dir.replace("\\", "/")
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Searching Google Scholar: {keyword}")

    pdf_links, metadata_list = get_pdf_links(keyword, max_results)
    if not pdf_links:
        raise ValueError("No PDF links found")

    logger.info(f"Found {len(pdf_links)} PDF links")
    logger.info("Started downloading...")

    success, failed, skipped_403, failed_downloads = await download_pdfs(pdf_links, metadata_list, output_dir)

    logger.info(f"Download complete: success={success}, skipped_403={skipped_403}, failed={failed_downloads}")
    return {
        "success": success + skipped_403,
        "failed": failed_downloads,
        "downloaded": success,
        "skipped_403": skipped_403,
        "failed_downloads": failed_downloads
    }




def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename).strip()



def get_pdf_links(keyword, max_results):
    pdf_links, metadatas = [], []
    start = 0

    while len(pdf_links) < max_results:
        data = search_google_scholar(keyword, start)
        if not data or "organic_results" not in data:
            break

        new_links, new_meta = extract_pdf_links(data)
        logger.debug(f"new_links {new_links}")
        pdf_links.extend(new_links)
        metadatas.extend(new_meta)

        pdf_links = pdf_links[:max_results]
        metadatas = metadatas[:max_results]
        start += 10

    return pdf_links, metadatas




def search_google_scholar(keyword, start=0):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_scholar",
        "q": keyword,
        "api_key": os.getenv("SERP_API_KEY"),
        "start": start
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"SerpAPI error: {e}")
        return {}





def extract_pdf_links(data):
    links, metadata = [], []
    for result in data.get("organic_results", []):
        for resource in result.get("resources", []):
            if resource.get("file_format") == "PDF":
                links.append(resource["link"])
                d = {
                    'title': result.get('title', 'Unknown'),
                    'source': result.get('link', ''),
                    'authors': [a.get('name', '') for a in result.get('publication_info', {}).get('authors', [])],
                    'year': result.get('publication_info', {}).get('year'),
                    'url': resource['link']
                }
                d['authors'] = list(set(d['authors']))
                metadata.append(d)
    return links, metadata





async def download_pdfs(pdf_links, metadatas, output_dir):
    num_downloaded = 0
    num_skipped_403 = 0
    num_failed = 0

    for ind, link in enumerate(pdf_links, start=1):
        metadata = metadatas[ind - 1]
        result = download_pdf_with_status(link, metadata, output_dir, ind)
        if result == "downloaded":
            num_downloaded += 1
        elif result == "skipped_403":
            num_skipped_403 += 1
        else:
            num_failed += 1

    return num_downloaded, num_failed, num_skipped_403, num_failed





def download_pdf_with_status(link, metadata, output_dir, ind):
    try:
        success = download(link, metadata, output_dir, ind)
        return "downloaded" if success else "failed"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.info(f"PDF #{ind} blocked by publisher (403) – skipping: {link}")
            return "skipped_403"
        else:
            logger.error(f"PDF #{ind} HTTP error {e.response.status_code}: {link}")
            return "failed"
    except Exception as e:
        logger.error(f"Failed to download PDF #{ind} from {link}: {e}")
        return "failed"





def download(url, metadata: dict, dir_, ind):
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    headers = {'User-Agent': USER_AGENT, 'Accept': 'application/pdf'}
    file_path = None
    dir_ = dir_.replace("\\", "/").rstrip("/") + "/"
    base_name = os.path.basename(dir_.rstrip("/"))

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=60)
            
            
            if response.status_code == 403:
                raise requests.exceptions.HTTPError("403 Forbidden", response=response)

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
Fetched From: google_scholar
"""

            upload_text_file(path=txt_key, file=txt_content)
            logger.debug(f"Metadata uploaded: {txt_key}")

            
            with open(pdf_path_local, "wb") as f:
                f.write(response.content)

            upload_pdf_from_path(pdf_path_local)
            logger.debug(f"PDF uploaded: {pdf_path_local}")
            return True

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.warning(f"Timeout on attempt {attempt+1}, retrying in {wait}s: {url}")
                time.sleep(wait)
                continue
            logger.error(f"PDF #{ind} timed out after {max_retries} attempts")
            return False

        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 403:
                raise  
            logger.error(f"HTTP error {e.response.status_code} on attempt {attempt+1}")
            if attempt == max_retries - 1:
                return False
            time.sleep(2 ** attempt)

        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt+1}: {e}")
            if attempt == max_retries - 1:
                return False
            time.sleep(2 ** attempt)

        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Local file removed: {file_path}")
                except:
                    pass

        return False