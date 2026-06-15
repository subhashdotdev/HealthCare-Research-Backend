from sqlalchemy.orm import Session
from fastapi import HTTPException, Request, Depends
from schemas.auth_schemas import UserRegistrationRequest, UserLoginRequest
from schemas.token_schemas import TokenRequest
from models.user_model import User
from models.token_model import Token
from core import jwt
from core.utils.utility import hash_password, verify_password
from uuid import uuid4
from services.token_services import save_token
# from database import get_db




def user_registration(db: Session, userData: UserRegistrationRequest):
    existing_user = db.query(User).filter(User.email==userData.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email id already exsist!")
    
    hashed_password = hash_password(userData.password)
    
    db_user = User(name = userData.name, email = userData.email, password = hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token = jwt.create_access_token({"user_id": db_user.user_id})
    refresh_token = jwt.create_refresh_token({"user_id": db_user.user_id})
    data = refresh_token
   
    jwt_refresh_token = data.get('jwt_refresh_token')
    expires = data.get("expire")
    user_id = db_user.user_id
    
    token_data = TokenRequest(jwt_access_token = access_token, jwt_refresh_token= jwt_refresh_token, expires = expires)
    
    save_token(db , user_id ,token_data)
    return {"jwt_access_token":access_token, "jwt_refresh_token":jwt_refresh_token}





def user_login(db: Session, loginData: UserLoginRequest):
    existing_user = db.query(User).filter(User.email == loginData.email).first()
    if not existing_user or not verify_password(plain_password=loginData.password, hashed_password=existing_user.password):
        raise HTTPException(status_code=401, detail="Incorect email id or password!")
    
    user_id = existing_user.user_id
    access_token = jwt.create_access_token({"user_id": user_id})
    refresh_token_data = jwt.create_refresh_token({"user_id": user_id})  
    
    refresh_token  = refresh_token_data.get("jwt_refresh_token")  
    expire = refresh_token_data.get("expire")

    token_data = TokenRequest(jwt_access_token = access_token, jwt_refresh_token= refresh_token, expires = expire)
    
    save_token(db , user_id ,token_data)
    return {"jwt_access_token": access_token, "jwt_refresh_token": refresh_token}





def user_logout(db: Session, request: Request):
    
    print(request.state.user)
    user_id = request.state.user.get("user_id")
    print(user_id)
    existing_user = db.query(Token).filter(Token.user_id == user_id).first() 
    
    if existing_user:
        db.delete(existing_user)
        db.commit()
        return "You are successfully loged out!"
    else:
        return "No user found!"


    