import os, traceback, httpx
from urllib.parse import urlencode
from fastapi import HTTPException, APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.schemas.users_schema import UserCreate, UserCreateService, UserLogin, UserGetInfo, UserUpdate
from app.models.users_models import find_user_by_email, insert_user, find_user, find_user_by_id, update_user
from app.utils.jwt_util import jwt_decoder, jwt_encoder
from app.utils.user_util import default_user_info

router = APIRouter()

def temp_dummy_data(res: dict):
    res["borrow_count"] = 0
    res["lend_count"] = 0
    res["borrow_money"] = 1000
    res["lend_money"] = 4000


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

        res = default_user_info(res)

        return {"access_token": access_token, "refresh_token": refresh_token, "my_info": res}
    except Exception as e:
        traceback.print_exc()
        print(str(e))
        return HTTPException(status_code=400, detail="Login failed")


@router.get("/users/login/kakao")
def kakaologin():
    client_id = os.environ.get('KAKAO_REST_API_KEY')
    redirect_uri = os.environ.get('KAKAO_REDIRECT_URI')

    config = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code"
    }
    params = urlencode(config)
    return RedirectResponse(url=f"https://kauth.kakao.com/oauth/authorize?{params}")


@router.get('/users/login/kakao/callback')
async def kakaocallback(request: Request):
    query = request.query_params
    code = query.get('code')
    clietn_id = os.environ.get('KAKAO_REST_API_KEY')
    redirect_uri = os.environ.get('KAKAO_REDIRECT_URI')
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
        information = json_response['kakao_account']
        nickname = information['profile']['nickname']
        email = information['email']
        if information['gender'] == 'female':
            female = True
        else:
            female = False
        user = UserCreate(id=email, nickname=nickname, female=female, type='kakao')
        # 이미 유저 존재하는지 확인하는 과정 필요
        try:
            res, message = find_user_by_email(UserGetInfo(id=email))
            if res == None:
                res = insert_user(user)
            try:
                # 예외처리 부분이 이상해서 일단 제거함
                message_access, access_token = jwt_encoder("access_token", res)
                message_refresh, refresh_token = jwt_encoder("refresh_token", res)

                res, message = find_user_by_id(UserGetInfo(id=res['_id']))

                res = default_user_info(res)

                return RedirectResponse(url=f"billimiut://account/{access_token}")
            except Exception as e:
                traceback.print_exc()
                print(str(e))
                return HTTPException(status_code=400, detail="Login failed")
        except Exception as e:
            traceback.print_exc()
            print(str(e))
            return HTTPException(status_code=400, detail="Signup failed")


@router.get("/users/my_info")
async def get_my_info(req: Request):
    auth_header = req.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    message, information = jwt_decoder(token, os.environ.get('JWT_SECRET_KEY_ACCESS'))
    id = information['data']['_id']
    res, message = find_user_by_id(UserGetInfo(id=id))

    res = default_user_info(res)

    # dummy data 넣기
    temp_dummy_data(res)

    return res


@router.put("/users/my_info")
async def put_my_info(user: UserUpdate):
    try:
        res = update_user(user)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Put my info failed")
    
@router.get("/users/token/{token}")
async def get_token(token: str):
    message, payload = jwt_decoder(token, os.environ.get('JWT_SECRET_KEY_ACCESS'))
    id = payload['data']['_id']

    message, refresh_token = jwt_encoder("refresh_token", payload['data'])

    res, message = find_user_by_id(UserGetInfo(id=id))

    res = default_user_info(res)

    return {"refresh_token": refresh_token, "my_info": res}
