from pydantic import BaseModel, EmailStr, Field



class UserRegistrationRequest(BaseModel):
    name: str = Field(description= "Name is required!")
    email: EmailStr = Field(description="Email is required!")
    password: str = Field(min_length= 8 , description="Password must have atleast 8 characters!")



class UserRegistrationResponse(BaseModel):
    jwt_access_token: str
    jwt_refresh_token: str



class UserLoginRequest(BaseModel):
    email: EmailStr = Field(description="Email is required!")
    password: str = Field(min_length=8, description="Password must have atleast 8 characters!")    




class UserLoginResponse(BaseModel):
    jwt_access_token: str
    jwt_refresh_token: str


    class Config:
        from_attributes = True  