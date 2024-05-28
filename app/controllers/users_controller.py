from fastapi import HTTPException
from app.schemas.users_schema import UserBase,UserCreate,UserLogin,UserGetInfo,UserUpdate
from app.models.users_models import insert_user,find_user,find_user_by_id,update_user
# from app.database.session import db

#login_user, signup_user, get_my_info, put_my_info

async def signup_user(user: UserCreate):
    try:
        # 중복여부 확인 필요
        res = insert_user(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Signup failed")

async def login_user(user: UserLogin):
    try:
        res = find_user(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Login failed")

async def get_my_info(user: UserGetInfo):
    try:
        res = find_user_by_id(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Get my info failed")
    
async def put_my_info(user: UserUpdate):
    try:
        res = update_user(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Put my info failed")