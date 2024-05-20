from fastapi import HTTPException
from app.schemas.users_schema import User
# from app.database.session import db

#login_user, signup_user, get_my_info, put_my_info

async def signup_user(user: User):
    try:
        print(user)
        return {"token": "success(수정 필요)"}
    except Exception:
        return HTTPException(status_code=400, detail="Signup failed")

async def login_user(user: User):
    try:
        print(user)
        return {"token": "success(수정 필요)"}
    except Exception:
        return HTTPException(status_code=400, detail="Login failed")

async def get_my_info():
    try:
        return "get my info"
    except Exception:
        return HTTPException(status_code=400, detail="Get my info failed")
    
async def put_my_info(user: User):
    try:
        return "put my info"
    except Exception:
        return HTTPException(status_code=400, detail="Put my info failed")