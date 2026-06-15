from pydantic import BaseModel, Field
from datetime import datetime, date, time, timedelta



class TokenRequest(BaseModel):
    jwt_access_token: str
    jwt_refresh_token: str
    expires: datetime



class TokenResponse(BaseModel):
    jwt_access_token: str
    jwt_refresh_token: str    
    
    
    class Config:
        from_attributes = True  