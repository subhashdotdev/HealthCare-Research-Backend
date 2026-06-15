from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from models.token_model import Token
from schemas.token_schemas import TokenRequest, TokenResponse
from models.token_model import Token




def save_token(db: Session, user_id, token_data: TokenRequest):
    user = db.query(Token).filter_by(user_id = user_id).first()
    if user:
        db_token = Token(user_id = user_id, jwt_access_token = token_data.jwt_access_token, jwt_refresh_token = token_data.jwt_refresh_token, expires_at = token_data.expires)
        db.add(db_token)
        db.commit()
    else:    
        db_token = Token(user_id = user_id, jwt_access_token = token_data.jwt_access_token, jwt_refresh_token = token_data.jwt_refresh_token, expires_at = token_data.expires)
        db.add(db_token)
        db.commit()

    return
