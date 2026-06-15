from fastapi import APIRouter, HTTPException, Depends, Request
from schemas.auth_schemas import UserRegistrationRequest, UserRegistrationResponse, UserLoginRequest, UserLoginResponse
from services.auth_services import user_registration, user_login, user_logout
from database.database import get_db
from sqlalchemy.orm import Session



router = APIRouter()



@router.post("/register", response_model=UserRegistrationResponse)
def create_new_user(userData: UserRegistrationRequest, db: Session = Depends(get_db)):
    return user_registration(db=db, userData=userData)



@router.post("/user_login", response_model=UserLoginResponse)
def login(userData: UserLoginRequest, db: Session = Depends(get_db)):
    return user_login(db=db, loginData = userData)



@router.get("/user_logout")
def logout(request: Request, db: Session = Depends(get_db)):
    return user_logout(db = db, request= request)

