from fastapi import APIRouter, HTTPException, Body
from app.schemas.users_schema import User
from app.controllers.users_controller import login_user, signup_user, get_my_info, put_my_info

router = APIRouter()

@router.post("/signup")
async def signup(user: User = Body(...)):
    return await signup_user(user)

@router.post("/login")
async def login(user: User = Body(...)):
    return await login_user(user)

# 이렇게 해도 되는게 맞는지? 얘는 수정이 좀 필요함.
@router.post("/login/kakao")
async def login_kakao(user: User = Body(...)):
    return await login_user(user)    

@router.get("/my_info")
async def get_my_info_route():
    return await get_my_info()

@router.put("/my_info")
async def put_my_info_route():
    return await put_my_info()