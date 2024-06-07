import os
from urllib.parse import urlencode
from fastapi import HTTPException, APIRouter, HTTPException, Body, Request
from fastapi.responses import RedirectResponse
import httpx
from app.models.post_models import find_post
from app.schemas.users_schema import UserCreate, UserCreateService, UserLogin,UserGetInfo,UserUpdate, UserCreateOauth
from app.models.users_models import insert_user,find_user,find_user_by_id,update_user, signup_check

from app.utils.jwt_util import jwt_decoder, jwt_encoder
# from app.database.session import db

#login_user, signup_user, get_my_info, put_my_info

router = APIRouter()

@router.post("/users/signup")
async def sign_up(user: UserCreateService):
    user = user.model_dump()
    user['type'] = "service"
    user = UserCreate(**user)
    try:
        res = insert_user(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Signup failed")

@router.post("/users/login")
async def login(user: UserLogin):
    try:
        res, message = find_user(user)
        # 예외처리 부분이 이상해서 일단 제거함
        message_access, access_token = jwt_encoder("access_token", res)
        message_refresh, refresh_token = jwt_encoder("refresh_token", res)
        del res['pw']
        del res['salt']
        del res['type']
        del res['token']

        # 포스팅 목록 불러오기
        borrow_list_id = res['borrow_list']
        lend_list_id = res['lend_list']

        borrow_list=[]
        lend_list=[]

        for item_id in borrow_list_id:
            item_info = find_post(item_id)
            borrow_list.append(item_info)
        for item_id in lend_list_id:
            item_info = find_post(item_id)
            lend_list.append(item_info)

        res['borrow_list'] = borrow_list
        res['lend_list'] = lend_list

        res ["borrow_count"] = 0
        res ["lend_count"] = 0
        res ["borrow_money"] = 1000
        res ["lend_money"] = 4000
        res ["borrow_list"] = ["시계", "자전거"]
        return {"access_token": access_token, "refresh_token": refresh_token, "my_info": res}
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
        user= UserCreate(id=email, nickname=nickname, female=female, type='kakao')
        # 이미 유저 존재하는지 확인하는 과정 필요
        try:
            res = insert_user(user)
            user = user.model_dump()
            message_access, access_token = jwt_encoder("access_token", user)
            message_refresh, refresh_token = jwt_encoder("refresh_token", user)
            return {"access_token": access_token, "refresh_token": refresh_token}
        except Exception:
            return HTTPException(status_code=400, detail="Signup failed")

@router.get("/users/my_info")
async def get_my_info(req: Request):
    auth_header= req.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    print(token)
    message, information = jwt_decoder(token, os.environ.get('JWT_SECRET_KEY_ACCESS'))
    id = information['data']['_id']
    res = find_user_by_id(UserGetInfo(id=id))

    # 필요 없는 정보 제거
    del res['pw']
    del res['salt']
    del res['type']
    del res['token']

    # 포스팅 목록 불러오기
    borrow_list_id = res['borrow_list']
    lend_list_id = res['lend_list']

    borrow_list=[]
    lend_list=[]

    for item_id in borrow_list_id:
        item_info = find_post(item_id)
        borrow_list.append(item_info)
    for item_id in lend_list_id:
        item_info = find_post(item_id)
        lend_list.append(item_info)

    res['borrow_list'] = borrow_list
    res['lend_list'] = lend_list

    # dummy data
    res ["borrow_count"] = 0
    res ["lend_count"] = 0
    res ["borrow_money"] = 1000
    res ["lend_money"] = 4000
    res ["borrow_list"] = ["시계", "자전거"]
    print(res)
    return res
    
@router.put("/users/my_info")
async def put_my_info(user: UserUpdate):
    try:
        res = update_user(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Put my info failed")