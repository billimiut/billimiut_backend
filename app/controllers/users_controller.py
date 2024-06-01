from fastapi import HTTPException, APIRouter, HTTPException, Body
from app.schemas.users_schema import UserBase,UserCreate,UserLogin,UserGetInfo,UserUpdate
from app.models.users_models import insert_user,find_user,find_user_by_id,update_user
# from app.database.session import db

#login_user, signup_user, get_my_info, put_my_info

router = APIRouter()

@router.post("/users/signup")
async def sign_up(user: UserCreate):
    try:
        # 중복여부 확인 필요
        res = insert_user(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Signup failed")

@router.post("/users/login")
async def login(user: UserLogin):
    try:
        res = find_user(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Login failed")

@router.post("/users/login/kakao")
async def login_kakao(user: UserLogin):
    try:
        res = find_user(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Login failed")

@router.get("/users/my_info")
async def get_my_info(user: UserGetInfo):
    try:
        res = find_user_by_id(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Get my info failed")
    
@router.put("/users/my_info")
async def put_my_info(user: UserUpdate):
    try:
        res = update_user(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Put my info failed")