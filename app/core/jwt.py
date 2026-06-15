from datetime import datetime, timedelta
from jose import jwt, JWTError
from core.settings import config
import uuid



SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
REFRESH_TOKEN_EXPIRE_DAYS = 7




def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    if "user_id" in to_encode and isinstance(to_encode["user_id"], uuid.UUID):
        to_encode["user_id"] = str(to_encode["user_id"])
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)




def create_refresh_token(data: dict) -> dict:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    if "user_id" in to_encode and isinstance(to_encode["user_id"], uuid.UUID):
        to_encode["user_id"] = str(to_encode["user_id"])
    to_encode.update({"exp": expire})
    jwt_refresh_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"jwt_refresh_token": jwt_refresh_token, "expire": expire}




def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None