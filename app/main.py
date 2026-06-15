from fastapi import FastAPI
from database.database import Base, engine
from routes import routes, auth_routes, user_routes
from core.middleware import JWTMiddleware
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


app = FastAPI()

# Base.metadata.create_all(bind=engine)


origins = [
    "http://34.122.93.169:8080",
    "http://34.46.180.54:8080",
    "http://34.136.249.59:5173",
    "http://34.42.162.219:5173",
    "http://localhost:5173",
    "http://34.173.193.149:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins= origins, 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)



@app.post("/")
async def test():
    return BASE_DIR
    


excluded_paths = ["/v1/auth/register", "/v1/auth/user_login","/docs","/openapi.json", "/"] 
app.add_middleware(JWTMiddleware, excluded_paths=excluded_paths)




app.include_router(auth_routes.router, prefix='/v1/auth', tags=['authentication-routes'])
app.include_router(routes.router, prefix='/v1/services', tags=['services-routes'])
app.include_router(user_routes.router, prefix='/v1/user', tags=['user-routes'])



if __name__ == "__main__":
    import uvicorn 
    uvicorn.run(app=app, port=8001)

