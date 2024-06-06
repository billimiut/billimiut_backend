import os
from urllib.parse import urlencode
from fastapi import HTTPException, APIRouter, HTTPException, Body, Request
from fastapi.responses import RedirectResponse
import httpx
from app.schemas.users_schema import UserCreate,UserLogin,UserGetInfo,UserUpdate, UserCreateOauth
from app.models.users_models import insert_user,find_user,find_user_by_id,update_user, signup_check

from app.utils.jwt_util import jwt_decoder, jwt_encoder
# from app.database.session import db

#login_user, signup_user, get_my_info, put_my_info

router = APIRouter()

@router.post("/users/signup")
async def sign_up(user: UserCreate):
    try:
        # 중복여부 확인 필요
        check = signup_check(user)['message']
        print(check)
        if check == "User not found":
            res = insert_user(user)
            return res
        else :
            return HTTPException(status_code=400, detail=check)
    except Exception:
        return HTTPException(status_code=400, detail="Signup failed")

@router.post("/users/login")
async def login(user: UserLogin):
    try:
        res, message = find_user(user)
        if res == None:
            return HTTPException(status_code=400, detail=message)
        print(res)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Login failed")

@router.get("/users/login/kakao")
def kakaologin():
    client_id = os.environ.get('KAKAO_REST_API_KEY')
    redirect_uri = "http://127.0.0.1:8000/login/kakao/callback"

    config = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code"
    }
    params = urlencode(config)
    print(params)

    return RedirectResponse(url=f"https://kauth.kakao.com/oauth/authorize?{params}")
    
@router.get('/login/kakao/callback')
async def kakaocallback(request: Request):
    query = request.query_params
    code = query.get('code')
    clietn_id = os.environ.get('KAKAO_REST_API_KEY')
    redirect_uri = "http://127.0.0.1:8000/login/kakao/callback"
    client_secret = os.environ.get('KAKAO_CLIENT_SECRET')

    config = {
        "grant_type": "authorization_code",
        "client_id": clietn_id,
        "redirect_uri": redirect_uri,
        "code": code,
        "client_secret": client_secret
    }
    params = urlencode(config)

    async with httpx.AsyncClient() as client:
        response = await client.post(f"https://kauth.kakao.com/oauth/token?{params}")
        rbody = response.json()
        print(rbody)
        access_token = rbody['access_token']
        url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        }

        response = await client.post(url, headers=headers)
            
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
        json_response = response.json()
        print(json_response)
        information = json_response['kakao_account']
        nickname = information['profile']['nickname']
        email = information['email']
        if information['gender'] == 'female':
            female = True
        else:
            female = False
        user= UserCreateOauth(id=email, nickname=nickname, female=female)
        user = user.model_dump()
        message_access, access_token = jwt_encoder("access_token", user)
        message_refresh, refresh_token = jwt_encoder("refresh_token", user)
        return {"access_token": access_token, "refresh_token": refresh_token}



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