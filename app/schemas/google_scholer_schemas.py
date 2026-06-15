from pydantic import BaseModel



class GoogleScholerRetriverRequest(BaseModel):
    project_name: str
    country: str 
    patient_cohort: str
    search_terms: list | str
    operators: list | str
    max_pdfs: int