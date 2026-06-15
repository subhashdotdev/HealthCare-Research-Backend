from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from models.search_model import Search
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse
from schemas.search_schemas import DeleteRecentSearchRequest





def add_search_term(user_id:str, term:str, db:Session):
    try:
        db_search = Search(user_id = user_id, search_term = term)
        db.add(db_search)
        db.commit()
        db.refresh(db_search)
        return True
    except SQLAlchemyError as e:
        print(f"Error: {str(e)}")
        return False 





async def user_recent_searches(request:Request, db:Session):
    user_id = request.state.user.get("user_id")
    try:
        searches = db.query(Search).filter(Search.user_id == user_id).all()
        if searches is None:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="User not found!")
        else:
            return searches
    except SQLAlchemyError as e:
        return {"Error": str(e)}    





def delete_specific_recent_search(data:DeleteRecentSearchRequest, db:Session):
    search_id = data.search_id
    try:
        search = db.query(Search).filter(Search.search_id == search_id).delete() 
        db.commit()
        if search == 0:
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail="search not found!")
        else:
            return JSONResponse( status_code= status.HTTP_200_OK, content="Search deleted successfully!")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail= str(e))   