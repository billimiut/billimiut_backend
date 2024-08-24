import traceback
from bson import ObjectId
from app.schemas.chat_schema import Message
from ..db.session import client

collection = 'chat'

def insert_chat(chat: Message):
    try:        
        chat = chat.model_dump()

        post_id = chat['post_id']
        sender_id = chat['sender_id']
        receiver_id = chat['receiver_id']

        # 변경 시 적용할 코드
        users = '_'.join(sorted([sender_id, receiver_id]))
        chat_id = '_'.join([post_id, users])

        # 기존코드
        # chat_id = ':'.join(sorted([sender_id, receiver_id]))

        new_chat = {
            "sender_id": sender_id,
            "message": chat["message"],
            "time": chat["time"]
        }

        response = client[collection].find_one({"_id": chat_id})
        if response:
            client[collection].update_one(
                {"_id": chat_id},
                {"$push": {"message": new_chat}}
            )
        else:
            client[collection].insert_one(
                {"_id": chat_id, "message": [new_chat], "user": [sender_id, receiver_id], "post_status": "published"}
            )
            client['user'].update_one(
                {"_id": ObjectId(sender_id)},
                {"$addToSet": {"chat_list": chat_id}},
                upsert=True
            )
            client['user'].update_one(
                {"_id": ObjectId(receiver_id)},
                {"$addToSet": {"chat_list": chat_id}},
                upsert=True
            )
        return True
    except Exception as e:
        traceback.print_exc()
        print(str(e))
        return False

def find_chat(chat_id: str):
    try:
        response = client[collection].find_one({"_id": chat_id})
        if response:
            return response
        else:
            return {"error": "Chat not found"}
    except Exception as e:
        print(e)
        return {"error": "Find failed"}
    
def get_chat_by_user_id(user_id:str):
    chats = list(client[collection].find({"user": user_id}))
    chat_ids = [str(chat['_id']) for chat in chats]

    return chat_ids

def find_chat_by_post_id(post_id: str):
    chats = list(client[collection].find())
    related_chat = list()
    for chat in chats:
        chat_id = chat["_id"]
        chat_info = chat_id.split('_')
        post_info = chat_info[0]
        if post_info == post_id:
            related_chat.append(chat_id)
    return related_chat

def delete_chat(chat_id: str):
    client[collection].delete_one({"_id": chat_id})
    return True

def update_related_post_status(chat_id: str):
    client[collection].update_one({"_id": chat_id},{"$set": {"post_status": "deleted"}})