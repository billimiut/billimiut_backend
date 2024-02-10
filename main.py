import os, json
from fastapi import FastAPI, HTTPException, File, UploadFile, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse # websocket test를 위한 code
from pydantic import BaseModel
from firebase_admin import credentials, storage, firestore, exceptions, initialize_app, auth
from typing import List, Dict, Optional
from datetime import datetime, timedelta

#cred = credentials.Certificate("/mnt/c/Users/USER/billimiut/billimiut_backend/billimiut-firebase-adminsdk-cr23b-980ffebf27.json")
cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "billimiut-firebase-adminsdk-cr23b-980ffebf27.json"))
default_app = initialize_app(cred, {
    'storageBucket': 'billimiut.appspot.com'
})
db = firestore.client()


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Websocket Demo</title>
           <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">

    </head>
    <body>
    <div class="container mt-3">
        <h1>FastAPI WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" class="form-control" id="messageText" autocomplete="off"/>
            <button class="btn btn-outline-primary mt-2">Send</button>
        </form>
        <ul id='messages' class="mt-5">
        </ul>
        
    </div>
    
        <script>
            var client_id = "JWguSs0WqJcdFWtwzrvYVJdSN8k2"
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class GeoPoint(BaseModel):
    latitude: float = 0.0
    longitude: float = 0.0

# category_id <- 일단 category: str으로 대체
class Post(BaseModel):
    post_id: str = ""
    writer_id: str = ""
    title: str
    item: str
    category: str # 변경
    image_url: List[str]
    money: int
    borrow: bool
    description: str
    emergency: bool
    start_date: datetime
    end_date: datetime
    location_id: str = ""
    female: bool
    status: str = "게시"
    borrower_user_id: Optional[str] = None
    lender_user_id: Optional[str] = None

class Login(BaseModel):
    id: str
    pw: str

class Login_Token(BaseModel):
    login_token: str

class User(BaseModel):
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
    chat_list: List[str] = []

class Nickname(BaseModel):
    user_id: str
    nickname: str

class ImageUrl(BaseModel):
    user_id: str
    image_url: str

class User_Location(BaseModel):
    user_id: str
    location: str

class Location(BaseModel):
    location_id: str = ""
    map: GeoPoint = GeoPoint()
    address: str = ""
    detail_address: str = ""
    name: str = ""
    dong: str = ""

class Add_Post(BaseModel):
    user_id: str
    post: Post
    location: Location

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    async def disconnect(self, client_id: str):
        websocket = self.active_connections[client_id]
        await websocket.close()
        del self.active_connections[client_id]

    async def send_personal_message(self, message: str, receiver_id: str):
        websocket = self.active_connections.get(receiver_id)
        if websocket:
            await websocket.send_text(message)

manager = ConnectionManager()

class Message(BaseModel):
    sender_id: str
    receiver_id: str
    content: str
    time: str = datetime.now().isoformat()

app = FastAPI()

# websocket test를 위한 code
@app.get("/")
async def get():
    return HTMLResponse(html)

#ok
@app.post("/login")
async def login(user: Login = Body(...)):
    print("login")
    try:
        user_record = auth.get_user_by_email(user.id)
    except Exception:
        return {"message": "0"}
    if not user_record:
        return {"message": "0"}
    return {"message": "1", "login_token": user_record.uid}

#ok
@app.post("/signup")
async def signup(user: User = Body(...)):
    try:
        user_record = auth.create_user(
            email=user.id,
            password=user.pw,
            display_name=user.nickname
        )
        user_data = user.dict()
        user_data['user_id'] = user_record.uid
        db.collection('user').document(user_record.uid).set(user_data)
    except exceptions.FirebaseError:
        raise HTTPException(status_code=400, detail="User creation failed")
    return {"message": "User successfully created"}

#ok
@app.post("/set_nickname")
async def set_nickname(nickname_data: Nickname = Body(...)):
    user_ref = db.collection('user').document(nickname_data.user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_ref.update({"nickname": nickname_data.nickname})
    return {"message": "Nickname successfully updated"}

#ok
@app.post("/set_image_url")
async def set_image_url(image_url_data: ImageUrl = Body(...)):
    user_ref = db.collection('user').document(image_url_data.user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_ref.update({"image_url": image_url_data.image_url})
    return {"message": "Image URL successfully updated"}

#ok
@app.post("/set_location")
async def set_locations(location_data: User_Location = Body(...)):
    user_ref = db.collection('user').document(location_data.user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_ref.update({"locations": firestore.ArrayUnion([location_data.location])})
    return {"message": "Location successfully added"}

#ok
@app.post("/my_info")
async def my_info(user: Login_Token = Body(...)):
    doc_ref = db.collection('user').document(user.login_token)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()  
    else:
        raise HTTPException(status_code=404, detail="User not found in Firestore")


@app.get("/get_post")
async def get_post(post_id: str):
    post_ref = db.collection('post').document(post_id) # post_id에 해당하는 post 가져옴
    post_doc = post_ref.get()

    if post_doc.exists:
        post = post_doc.to_dict() # post 딕셔너리
        
        # post에서의 writer_id로 user에 접근해서 nickname, image_url 뽑아와서 post에 추가    
        user = db.collection('user').document(post['writer_id']).get().to_dict() # user table
        nickname = user['nickname']
        profile = user['image_url']
        post['nickname'] = nickname
        post['profile'] = profile

        # post에서의 location_id로 location에 접근해서 address, detail_address, name, map, dong 초기화
        location = db.collection('location').document(post['location_id']).get().to_dict() # location table
        address = location['address']
        detail_address = location['detail_address']
        name = location['name']
        map = location['map']
        dong = location['dong']
        post['address'] = address
        post['detail_address'] = detail_address
        post['name'] = name
        post['map'] = map
        post['dong'] = dong

        return post
    else:
        return {"error": "Document does not exist"}

#ok
@app.get("/get_posts")
async def read_posts():
    print("get_posts")
    docs = db.collection('post').stream()
    result = []
    for doc in docs:
        post = doc.to_dict()

        # post에서의 writer_id로 user에 접근해서 nickname, image_url 뽑아와서 post에 추가    
        user = db.collection('user').document(post['writer_id']).get().to_dict() # user table
        nickname = user['nickname']
        profile = user['image_url']
        post['nickname'] = nickname
        post['profile'] = profile

        # post에서의 location_id로 location에 접근해서 address, detail_address, name, map, dong 초기화
        location = db.collection('location').document(post['location_id']).get().to_dict() # location table
        address = location['address']
        detail_address = location['detail_address']
        name = location['name']
        map = location['map']
        dong = location['dong']
        post['address'] = address
        post['detail_address'] = detail_address
        post['name'] = name
        post['map'] = map
        post['dong'] = dong

        print(result)

        #selected_fields = {field: post.get(field, None) for field in ['post_id', 'writer_id', 'title', 'description', 'item', 'image_url', 'money', 'borrow', 'description', 'emergency', 'start_date', 'end_date', 'location_id', 'female', 'status', 'category_id', 'borrower_user_id', 'lender_user_id', 'chat_list']}
        result.append(post)
    return result


@app.get("/get_location")
async def get_location(location_id: str):
    doc_ref = db.collection('location').document(location_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return {"error": "Document does not exist"}


@app.post("/add_post")
async def add_post(data: Add_Post):
    user_id = data.user_id
    post = data.post
    location = data.location
    geopoint = firestore.GeoPoint(data.location.map.latitude, data.location.map.longitude)

    # 빌린 사람/빌려준 사람 초기화
    if post.borrow:
        post.borrower_user_id = user_id
        post.lender_user_id = ""
    else:
        post.lender_user_id = user_id
        post.borrower_user_id = ""

    doc_ref1 = db.collection('post').document()
    doc_ref2 = db.collection('location').document()
    
    try:
        post_dict = post.dict()
        post_dict["writer_id"] = user_id
        post_dict["post_id"] = doc_ref1.id
        post_dict["location_id"] = doc_ref2.id
        doc_ref1.set(post_dict)

        location_dict = location.dict()
        location_dict["location_id"] = doc_ref2.id
        location_dict["map"] = geopoint
        doc_ref2.set(location_dict)

    except Exception as e:
        raise HTTPException(status_code=400, detail="An error occurred while adding the Post.")
    return {"message": "Post successfully added"}


@app.post("/upload_image")
async def upload_image(images: List[UploadFile] = File(...)):
    urls = []

    for image in images:
        if not (image.content_type == 'image/jpeg' or image.content_type == 'image/jpg' or image.content_type == 'image/png'):
            raise HTTPException(status_code=400, detail="Invalid file type.")
        
        fileName = f'{datetime.now().timestamp()}.jpg'
        blob = storage.bucket().blob(f'post_images/{fileName}')
        blob.upload_from_file(image.file, content_type=image.content_type)

        url = blob.generate_signed_url(timedelta(days=365))
        urls.append(url)

    return {"urls": urls}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            message = Message(**data_json, time = datetime.now().isoformat())
            chat_id = ''.join(sorted([message.sender_id, message.receiver_id]))
            db.collection('chats').document(chat_id).collection('messages').add(message.dict())
            await manager.send_personal_message(f"Message text was: {message.content}", message.receiver_id)

            # Update the chat_list field in each user's document
            user_doc_A = db.collection('user').document(message.sender_id)
            user_doc_A.set({"chat_list": firestore.ArrayUnion([message.receiver_id])}, merge=True)
            user_doc_B = db.collection('user').document(message.receiver_id)
            user_doc_B.set({"chat_list": firestore.ArrayUnion([message.sender_id])}, merge=True)
    except WebSocketDisconnect:
        await manager.disconnect(client_id)


@app.get("/get_messages/{chat_id}")
async def get_messages(chat_id: str):
    messages = db.collection('chats').document(chat_id).collection('messages').stream()
    return {"messages": [doc.to_dict() for doc in messages]}