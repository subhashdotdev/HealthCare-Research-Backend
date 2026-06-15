from pydantic import BaseModel



class DeleteRecentSearchRequest(BaseModel):
    search_id: str