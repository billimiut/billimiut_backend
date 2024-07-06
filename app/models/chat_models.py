from app.schemas.chat_schema import Message
from ..db.session import client

collection = 'chat'

def insert_chat(chat: Message):
    try:        
        chat = chat.model_dump()
        print(chat)
        print("~~!")
        chat_id = ':'.join(sorted([chat['sender_id'], chat['receiver_id']]))
        response = client[collection].find_one({"_id": chat_id})
        if response:
            client[collection].update_one(
                {"_id": chat_id},
                {"$push": {"message": chat}}
            )
        else:
            client[collection].insert_one(
                {"_id": chat_id, "message": [chat]}
            )
        client[collection].update_one(
            {"_id": chat["sender_id"]},
            {"$addToSet": {"chat_list": f"{chat['receiver_id']}-{chat['post_id']}"}},
            upsert=True
        )
        client[collection].update_one(
            {"_id": chat["receiver_id"]},
            {"$addToSet": {"chat_list": f"{chat['sender_id']}-{chat['post_id']}"}},
            upsert=True
        )
        return True
    except Exception as e:
        print(e)
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