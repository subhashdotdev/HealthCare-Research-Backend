from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from models.user_model import User
from sqlalchemy.exc import SQLAlchemyError
from schemas.user_schemas import UserUpdateRequest, ChangeUserPasswordRequest
from core.utils.utility import hash_password





def get_user_details_by_id(db: Session, request: Request):
    user_id = request.state.user.get("user_id")
    print("user_id", user_id)
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="User not found!")
        else:
            return user
    except SQLAlchemyError as e:
        return {"Error": str(e)}    





def get_all_users(db: Session):
    try: 
        all_users = db.query(User).all()
        if not all_users:
            return JSONResponse(status_code= status.HTTP_404_NOT_FOUND, content="No user data found!")
        else:
            
            return all_users
    except SQLAlchemyError as e:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail="Somthing wrong happend. Please try again later!")
           




async def user_delete(db: Session, request: Request):
    user_id = request.state.user.get("user_id")
    print("user_id", user_id)
    try:
        user = db.query(User).filter(User.user_id == user_id).delete() 
        db.commit()
        if user == 0:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="User not found!")
        else:
            return JSONResponse( status_code= status.HTTP_200_OK, content="user deleted successfully!")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail= str(e))     
    




def user_update(db: Session, request: Request, data: UserUpdateRequest):
    user_id = request.state.user.get("user_id")
    try:
        update_data = User(name = data.name, email = data.email)
        user = db.query(User).filter(User.user_id == user_id).update({"name": data.name, "email": data.email})
        db.commit()
        if user == 0:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="User not found!")
        else:
            return JSONResponse(status_code= status.HTTP_200_OK, content="User updated successfully!")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong. Please try again!")    
        





def user_password_change(request:Request, data: ChangeUserPasswordRequest, db:Session):
    user_id = request.state.user.get("user_id")
    hashed_password = hash_password(data.password)

    try:
        update_data = {"password": hashed_password}
        user = db.query(User).filter(User.user_id == user_id).update(update_data)
        db.commit()
        if user == 0:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="User not found!")
        else:
            return JSONResponse(status_code= status.HTTP_200_OK, content="User password updated successfully!")
    except SQLAlchemyError as e:
        db.rollback()
        print("Error:", str(e))
        raise HTTPException(status_code= status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Something went wrong. Please try again!")    

    