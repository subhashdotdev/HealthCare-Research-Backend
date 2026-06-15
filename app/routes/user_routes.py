from fastapi import APIRouter, Request, Depends
from services.user_services import get_user_details_by_id, user_update, user_password_change
from database.database import get_db
from sqlalchemy.orm import Session
from schemas.user_schemas import UserUpdateRequest, ChangeUserPasswordRequest


router = APIRouter()


@router.post("/get_all_users")
async def get_all_users():
    pass


@router.get("/get_user_details")
async def get_user_details(request: Request, db: Session = Depends(get_db)):
    return get_user_details_by_id(db=db, request= request)


@router.post("/user_update")
async def user_updates(request:Request, data: UserUpdateRequest, db: Session = Depends(get_db)):
    return user_update(db=db, request=request, data=data)


@router.post("/change_password")
async def change_password(request:Request, data: ChangeUserPasswordRequest, db: Session = Depends(get_db)):
    return user_password_change(request=request, data=data, db=db)


@router.post("/user_delete")
async def user_delete():
    pass