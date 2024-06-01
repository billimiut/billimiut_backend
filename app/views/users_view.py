from fastapi import APIRouter, HTTPException, Body
from app.schemas.users_schema import UserBase, UserCreate, UserLogin,UserGetInfo, UserUpdate
from app.controllers.users_controller import login_user, signup_user, get_my_info, put_my_info

router = APIRouter()

@router.post("/users/signup")
async def signup(user: UserCreate = Body(...)):
    return await signup_user(user)

@router.post("/users/login")
async def login(user: UserLogin = Body(...)):    
    return await login_user(user)

@router.post("/users/login/kakao")
async def login_kakao(user: UserBase = Body(...)):
    return await login_user(user)    

@router.get("/users/my_info")
async def get_my_info_route(user: UserGetInfo = Body(...)):
    return await get_my_info(user)

@router.put("/users/my_info")
async def put_my_info_route(user: UserUpdate = Body(...)):
    return await put_my_info(user)

## deprecated ##
## 나중에 이전 API들 연결해주는 그런걸로 사용할 수 있을 듯 ##