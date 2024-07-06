from fastapi import HTTPException, APIRouter, HTTPException, Body, UploadFile, WebSocket, WebSocketDisconnect
from app.schemas.chat_schema import manager, Message
from app.models.chat_models import insert_chat,find_chat
import json
from datetime import datetime
router = APIRouter()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            message = Message(**data_json, time = datetime.now().isoformat())
            print(f"Message content: {message.model_dump()}")
            if insert_chat(message):
                await manager.send_personal_message(message.message, message.time, message.sender_id, message.receiver_id, message.post_id)            
            # db.collection('chats').document(chat_id).collection('messages').add(message.dict())
            # await manager.send_personal_message(message.message, message.time, message.sender_id, message.receiver_id, message.post_id)
            # user_doc_A = db.collection('user').document(message.sender_id)
            # user_doc_A.set({"chat_list": firestore.ArrayUnion([f"{message.receiver_id}-{message.post_id}"])}, merge=True)
            # user_doc_B = db.collection('user').document(message.receiver_id)
            # user_doc_B.set({"chat_list": firestore.ArrayUnion([f"{message.sender_id}-{message.post_id}"])}, merge=True)
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
        # await manager.broadcast(f"Client #{client_id} left the chat")

@router.get("/get_messages/{chat_id}")
async def get_messages(chat_id: str):
    try:
        return find_chat(chat_id)
    except Exception:
        return HTTPException(status_code=400, detail="Get messages failed")
