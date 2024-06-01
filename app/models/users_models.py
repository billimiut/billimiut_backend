from datetime import timedelta, timezone, datetime
from bson import ObjectId

from ..db.session import client
from ..schemas.users_schema import UserBase, UserCreate, UserLogin,UserGetInfo, UserUpdate

collection = 'user' # user로 수정해야하나?
collection_temp = 'user_temp'

def insert_user(user: UserCreate):
    try:
        # 여기서 추가정보를 어떻게 넣을지 결정해야 함.
        user = user.model_dump()
        response = client[collection].find_one({"id": user["id"]})        
        if response:
            return {"error": "User already exists"}
        else:
            response = client[collection].insert_one(user)            
            return {"_id": str(response.inserted_id)}
    except Exception as e:
        print(e)
        return {"error": "Insert failed"}
    
def find_user(user: UserLogin):
    try:
        user = user.model_dump()
        response = client[collection].find_one(user)
        if response:
            response["_id"] = str(response["_id"])
            return response
        else:
            return {"error": "User not found"}
    except Exception as e:
        print(e)
        return {"error": "Find failed"}
    
def find_user_by_id(user:UserGetInfo):
    try:
        user = user.model_dump()
        response = client[collection].find_one(user)
        if response:
            response["_id"] = str(response["_id"])
            return response
        else:
            return {"error": "User not found"}
    except Exception as e:
        print(e)
        return {"error": "Find failed"}

def update_user(user: UserUpdate):
    try:
        user = user.model_dump()
        response = client[collection].find_one({"id": user["id"]})
        if response:
            response = client[collection].update_one({"id": user["id"]}, {"$set": {"nickname": user["nickname"]}})
            return {"message":response.modified_count} # 수정된 갯수. 0이면 수정된게 없다는건데, 이것도 에러처리 해야되나?
        else:
            return {"error": "User not found"}
    except Exception as e:
        print(e)
        return {"error": "Update failed"}