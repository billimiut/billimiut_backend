from datetime import timedelta, timezone, datetime
from bson import ObjectId

from ..db.session import client
from ..schemas.users_schema import UserBase

collection = 'billimiut'
collection_temp = 'billimiut_temp'

def insert_user(user: UserBase):
    try:
        user = user.model_dump()
        response = client[collection].insert_one(user)
        return {"_id": str(response.inserted_id)}
    except Exception as e:
        print(e)
        return {"error": "Insert failed"}