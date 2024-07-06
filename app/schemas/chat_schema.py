from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import WebSocket

import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    async def disconnect(self, client_id: str):
        websocket = self.active_connections.get(client_id)
        if websocket is not None:
            await websocket.close()
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: str, time: str, sender_id: str, receiver_id: str, post_id: str):
        websocket = self.active_connections.get(receiver_id)
        if websocket:
            data = {
                "message": message,
                "time": time,
                "sender_id": sender_id,
                "post_id": post_id
            }
            await websocket.send_text(json.dumps(data))

manager = ConnectionManager()

class Message(BaseModel):
    sender_id: str
    receiver_id: str
    message: str
    time: str
    post_id: str

