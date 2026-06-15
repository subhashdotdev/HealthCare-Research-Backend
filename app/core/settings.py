import os
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path


load_dotenv(override=True) 


BASE_DIR = Path(__file__).resolve().parent.parent
BASE_PATH = os.getenv("BASE_PATH")
SRC_DIR = os.path.join(BASE_DIR, 'src')
INPUT_DIR = os.path.join(BASE_DIR, 'input')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')




class Config(BaseModel):
    PUBMED_SEARCH_URL : str = os.getenv("PUBMED_SEARCH_URL")
    BASE_URL : str = os.getenv("BASE_URL")
    USER_AGENT : str = os.getenv("USER_AGENT")
    CHUNK_SIZE : str = os.getenv("CHUNK_SIZE")
    RETRIES : str = os.getenv("RETRIES")
    BACKOFF_FACTOR :str = os.getenv("BACKOFF_FACTOR")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION")
    BUCKET_NAME: str = os.getenv("BUCKET_NAME")

    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    GCP_BUCKET_NAME: str = os.getenv("GCP_BUCKET_NAME")

config = Config()