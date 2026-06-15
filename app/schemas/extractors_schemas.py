from pydantic import BaseModel
from typing import Optional
from fastapi import Form




class TermExtractorRequest(BaseModel):
    article_type: str = Form(...)
    surgical_device_name: Optional[str] = Form(...)
    surgical_technique: Optional[str] = Form(...)
    diagnostic_test_type: Optional[str] = Form(...)
    diagnostic_test_name: Optional[str] = Form(...)
    diagnostic_sample_type: Optional[str] = Form(...)
    diagnostic_technique: Optional[str] = Form(...)




class TableExtractorRequest(BaseModel):
    project_name: str = Form(...)
    