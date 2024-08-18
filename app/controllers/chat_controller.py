import traceback
import json

from datetime import datetime
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from app.schemas.chat_schema import manager, Message
from app.models.chat_models import insert_chat,find_chat

router = APIRouter()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            message = Message(**data_json, time=datetime.utcnow().isoformat())
            print(f"Message content: {message.model_dump()}")
            if insert_chat(message):
                await manager.send_personal_message(message.message, message.time, message.sender_id, message.receiver_id, message.post_id)
    except WebSocketDisconnect:
        await manager.disconnect(client_id)


@router.get("/get_messages/{chat_id}")
async def get_messages(chat_id: str):
    try:

        chat_info = find_chat(chat_id)
        user = chat_info['user']
        user_1 = user[0]
        user_2 = user[1]
        messages = chat_info['message']

        for message in messages:
            if message['sender_id'] == user_1:
                message['receiver_id'] = user_2
            else:
                message['receiver_id'] = user_1
            message['post_id'] = chat_id.split('_')[0]
            
        return messages
    except Exception as e:
        traceback.print_exc()
        print(str(e))
        return HTTPException(status_code=400, detail="Get messages failed")
