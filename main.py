from fastapi import FastAPI, HTTPException, Body, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from firebase_admin import credentials, firestore, initialize_app, auth
from typing import List, Dict, Optional
from datetime import datetime

cred = credentials.Certificate("/mnt/c/Users/USER/billimiut/billimiut_backend/billimiut-firebase-adminsdk-cr23b-980ffebf27.json")
default_app = initialize_app(cred)
db = firestore.client()

class Item(BaseModel):
    post_id: str
    title: str
    item: str
    image_url: List[str]
    money: int
    borrow: bool
    description: str
    emergency: bool
    start_date: datetime
    end_date: datetime
    location_id: int
    femail: bool
    status: str = "게시"
    keyword_id: str
    borrower_user_id: Optional[str] = None
    lender_user_id: Optional[str] = None

class User(BaseModel):
    id: str
    pw: str

class Login_Token(BaseModel):
    login_token: str

class SignUp_User(BaseModel):
    id: str
    pw: str
    nickname: str
    user_id: str = ""
    posts: List[str] = []
    borrow_list: List[str] = []
    lend_list: List[str] = []
    temperature: float = 36.5
    total_money: int = 0
    borrow_count: int = 0
    image_url: str = ""
    keywords : List[str] = []
    lend_count: int = 0
    locations: List[str] = []

class Nickname(BaseModel):
    uid: str
    nickname: str

class ImageUrl(BaseModel):
    uid: str
    image_url: str


class Location(BaseModel):
    uid: str
    location_id: str


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    async def disconnect(self, client_id: str):
        del self.active_connections[client_id]

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)


class Message(BaseModel):
    sender_id: str
    receiver_id: str
    content: str


manager = ConnectionManager()
app = FastAPI()


@app.post("/login")
async def login(user: User = Body(...)):
    print("login")
    try:
        user_record = auth.get_user_by_email(user.id)
    except Exception:
        return {"message": "0"}
    if not user_record:
        return {"message": "0"}
    return {"message": "1", "login_token": user_record.uid}


@app.post("/signup")
async def signup(user: SignUp_User = Body(...)):
    try:
        user_record = auth.create_user(
            email=user.id,
            password=user.pw,
            display_name=user.nickname
        )
        user_data = user.dict()
        user_data['user_id'] = user_record.uid
        db.collection('user').document(user_record.uid).set(user_data)
    except auth.AuthError:
        raise HTTPException(status_code=400, detail="User creation failed")
    return {"message": "User successfully created"}


@app.post("/set_nickname")
async def set_nickname(nickname_data: Nickname = Body(...)):
    user_ref = db.collection('user').document(nickname_data.uid)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_ref.update({"nickname": nickname_data.nickname})
    return {"message": "Nickname successfully updated"}


@app.post("/set_image_url")
async def set_image_url(image_url_data: ImageUrl = Body(...)):
    user_ref = db.collection('user').document(image_url_data.uid)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_ref.update({"image_url": image_url_data.image_url})
    return {"message": "Image URL successfully updated"}


@app.post("/set_locations")
async def set_locations(location_data: Location = Body(...)):
    user_ref = db.collection('user').document(location_data.uid)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_ref.update({"locations": firestore.ArrayUnion([location_data.location_id])})
    return {"message": "Location ID successfully added"}


@app.post("/my_info")
async def my_info(user: Login_Token = Body(...)):
    doc_ref = db.collection('user').document(user.login_token)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()  
    else:
        raise HTTPException(status_code=404, detail="User not found in Firestore")


@app.get("/get_posts")
async def read_items():
    print("get_posts")
    docs = db.collection('post').stream()
    result = []
    for doc in docs:
        data = doc.to_dict()
        selected_fields = {field: data.get(field, None) for field in ['post_id', 'title', 'description', 'item', 'image_url', 'money', 'borrow', 'description', 'emergency', 'start_date', 'end_date', 'location_id', 'female', 'status', 'keyword_id', 'borrower_user_id', 'lender_user_id']}
        result.append(selected_fields)
    return result


@app.post("/add_post")
async def add_item(user_id: str, item: Item):
    if item.borrow:
        item.borrower_user_id = user_id
    else:
        item.lender_user_id = user_id

    doc_ref = db.collection('post').document()
    try:
        doc_ref.set(item.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail="An error occurred while adding the item.")
    return {"message": "Item successfully added"}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = Message(sender_id=client_id, receiver_id='all', content=data)
            chat_id = ''.join(sorted([client_id, 'all'])) 
            db.collection('chats').document(chat_id).collection('messages').add(message.dict())
            await manager.send_message(f"Message text was: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(client_id)


@app.get("/get_messages/{chat_id}")
async def get_messages(chat_id: str):
    messages = db.collection('chats').document(chat_id).collection('messages').stream()
    return {"messages": [doc.to_dict() for doc in messages]}