from datetime import timedelta, datetime
import os
import jwt


def jwt_decoder(token: str, key: str):
    try:
        payload = jwt.decode(token, key, algorithms=['HS256'])
        return {"message": "Success"}, payload
    except jwt.ExpiredSignatureError:
        return {"message": "Token expired"}
    except jwt.InvalidTokenError:
        return {"message": "Invalid Token"}


def jwt_encoder(scope: str, data: dict):
    if scope == "access_token":
        time = timedelta(days=30)
        key = os.environ.get('JWT_SECRET_KEY_ACCESS')
    elif scope == "refresh_token":
        time = timedelta(days=60)
        key = os.environ.get('JWT_SECRET_KEY_REFRESH')
    else:
        return {"message": "Invalid scope"}
    payload = {
        "exp": datetime.utcnow() + time,
        "iat": datetime.utcnow(),
        "scope": scope,
        "data": data
    }
    token = jwt.encode(payload, key, algorithm='HS256')
    return {"message": "Success"}, token