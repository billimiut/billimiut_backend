from typing import Dict, Optional
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_ids: Dict[WebSocket, str] = {}  # WebSocket과 클라이언트 식별자의 매핑

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_ids[websocket] = client_id

    async def disconnect(self, websocket: WebSocket):
        client_id = self.client_ids.pop(websocket, None)
        if client_id:
            del self.active_connections[client_id]

    async def send_personal_message(self, sender_id: str, receiver_id: str, message: str):
        receiver_websocket = self.active_connections.get(receiver_id)
        if receiver_websocket:
            await receiver_websocket.send_text(f"Message from {sender_id}: {message}")

    async def get_client_id(self, websocket: WebSocket) -> Optional[str]:
        return self.client_ids.get(websocket)

"""
client_ids: WebSocket과 해당 클라이언트의 식별자를 매핑하는 딕셔너리입니다. 
이를 통해 송신자와 수신자를 추적할 수 있습니다.
get_client_id 메서드: WebSocket을 사용하여 
해당 WebSocket에 연결된 클라이언트의 식별자를 가져오는 메서드입니다.
이제 이 ConnectionManager 클래스를 사용하여 1:1 소통을 구현할 수 있습니다. 
송신자는 메시지를 보낼 때 자신과 수신자의 식별자를 지정하고, 
ConnectionManager를 사용하여 해당 수신자의 WebSocket을 가져와 메시지를 전송할 수 있습니다.
"""