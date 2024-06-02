from datetime import timedelta, timezone, datetime
from bson import ObjectId

from ..db.session import client
from ..schemas.post_schema import PostBase, PostUpdate

collection = 'post' # post로?
collection_temp = 'post_temp'

def insert_post(post: PostBase):
    try:
        post = post.model_dump()
        response = client[collection].insert_one(post)
        return {"_id": str(response.inserted_id)}
    except Exception as e:
        print(e)
        return {"error": "Insert failed"}

def find_post(post_id: str):
    try:
        response = client[collection].find_one({"_id": ObjectId(post_id)})
        if response:
            response['_id'] = str(response['_id'])
            return response
        else:
            return {"error": "Post not found"}
    except Exception as e:
        print(e)
        return {"error": "Find failed"}

def find_posts():
    try:
        response = list(client[collection].find())
        if response:
            for post in response:
                post['_id'] = str(post['_id'])
            return response
        else:
            return {"error": "Posts not found"}
    except Exception as e:
        print(e)
        return {"error": "Find failed"}
    
def update_post_status(post: PostUpdate):
    try:
        post = post.model_dump()
        print("hi")
        response = client[collection].find_one({"_id": ObjectId(post["post_id"])})
        print("hi")
        if response:
            response = client[collection].update_one({"_id": ObjectId(post["post_id"])}, {"$set": {"status": not response["status"]}})
            return {"message":response.modified_count} # 수정된 갯수.
        else:
            return {"error": "Post not found"}
    except Exception as e:
        print(e)
        return {"error": "Update failed"}
    
def erase_post(post_id: str):
    try:
        response = client[collection].delete_one({"_id": ObjectId(post_id)})
        return {"message":response.deleted_count} # 삭제된 갯수 반환.
    except Exception as e:
        print(e)
        return {"error": "Delete failed"}

def find_posts_by_user(user_id: str): # 'input' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string
    try: # 위와 같은 에러가 뜨는데, 해결방법을 잘 모르겠음. 나중에 해결하기.
        response = client[collection].find({
            "$or": [
                {"borrower_uuid": user_id, "borrow": True}, 
                {"lender_uuid": user_id, "borrow": False}
            ]
        })
        print(response)
        if response:
            return response
        else:
            return {"error": "Posts not found"}
    except Exception as e:
        print(e)
        return {"error": "Find failed"}
    
def find_posts_by_user_and_status(user_id: str, status: str):
    try:
        response = client[collection].find({"_id": user_id, "status": status}) # 이것도 결국 비슷한거라 나중에 해결하기.
        if response:
            return response
        else:
            return {"error": "Posts not found"}
    except Exception as e:
        print(e)
        return {"error": "Find failed"}

def update_post(post_id: str, post: PostBase):
    try:
        post = post.model_dump()
        response = client[collection].find_one({"_id": ObjectId(post_id)})
        if response:
            response = client[collection].update_one({"_id": ObjectId(post_id)}, {"$set": post})
            print(response)
            return {"message":response.modified_count} # 수정된 갯수.
        else:
            return {"error": "Post not found"}
    except Exception as e:
        print(e)
        return {"error": "Update failed"}