from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from core import jwt
from fastapi.responses import JSONResponse




class JWTMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, excluded_paths: list = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths
        
    async def dispatch(self, request: Request, call_next):
        for i in (self.excluded_paths):
            print("REQUEST TYPE:", request.method)
            if request.url.path == i:
               print("first")
               print(request.url.path)
               return await call_next(request)
            elif request.method == "OPTIONS":
                print("IN OPTION ")
                return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authorization header missing or not available"},
            )
        
        token = auth_header.split(" ")[1]
        payload = jwt.verify_token(token)
        if not payload:
            return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired token!"},
            )
        
        request.state.user = payload
        return await call_next(request)  

