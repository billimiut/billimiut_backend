import os, json, pytz, asyncio
from fastapi import FastAPI, HTTPException, File, UploadFile, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse # websocket test를 위한 code
from pydantic import BaseModel
from firebase_admin import credentials, storage, firestore, exceptions, initialize_app, auth
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from geopy.distance import geodesic

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
    image_url: List[str] =[]
    money: int
    borrow: bool
    description: str
    emergency: bool
    start_date: datetime
    end_date: datetime
    post_time: datetime
    female: bool
    status: str = "게시"
    borrower_user_id: Optional[str] = None
    lender_user_id: Optional[str] = None
    nickname: str
    profile: str = ""
    address: str = ""
    detail_address: str = ""
    name: str = ""
    map: GeoPoint = GeoPoint()
    dong: str = ""
    
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
    location: GeoPoint = GeoPoint()
    dong: str
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
    post_id: str
    message: str
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
        user_id = user_record.uid
        doc_ref = db.collection('user').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            my_info = doc.to_dict()
            borrow_list = my_info['borrow_list']
            lend_list = my_info['lend_list']
            chat_list = my_info['chat_list']

            result_borrow_list = []
            result_lend_list = []
            result_chat_list = []

            # borrow_list, lend_list 실제 post 정보로 채우기
            if borrow_list is not None:
                for post_id in borrow_list:
                    post = db.collection('post').document(post_id).get().to_dict() # post_id에 해당하는 post 가져옴
                    result_borrow_list.append(post)

            if lend_list is not None:
                for post_id in lend_list:
                    post = db.collection('post').document(post_id).get().to_dict() # post_id에 해당하는 post 가져옴
                    result_lend_list.append(post)

            # chat_list에 neighbor_id, post_id, neighbor_nickname, neighbor_profile, last_message, last_message_time
            if chat_list is not None:
                for chat in chat_list:
                    neighbor_chat_info = {}

                    neighbor_id, post_id = chat.split("-")
                    neighbor_chat_info['neighbor_id'] = neighbor_id
                    neighbor_chat_info['post_id'] = post_id

                    chatting_room = sorted([user_id, neighbor_id])
                    chatting_room = ''.join(chatting_room)
                    
                    # neighbor 정보 저장
                    neighbor = db.collection('user').document(neighbor_id).get().to_dict() # user table
                    neighbor_chat_info['neighbor_nickname'] = neighbor['nickname']
                    neighbor_chat_info['neighbor_profile'] = neighbor['image_url']

                    # chatting 정보 저장
                    collection_ref = db.collection('chats').document(chatting_room).collection('messages')
                    last_doc = next(collection_ref.order_by('time', direction=firestore.Query.DESCENDING).limit(1).stream()).to_dict()
                    neighbor_chat_info['last_message'] = last_doc['message']
                    neighbor_chat_info['last_message_time'] = last_doc['time']
                    result_chat_list.append(neighbor_chat_info)

            #chat_list
            my_info['borrow_list'] = result_borrow_list
            my_info['lend_list'] = result_lend_list
            my_info['chat_list'] = result_chat_list

            return my_info
        else:
            raise HTTPException(status_code=404, detail="User not found in Firestore")
    except Exception:
        return {"message": "An exception occurred."}

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
async def set_image_url(user_id: str, image: UploadFile = File(...)):
    user_ref = db.collection('user').document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    # storage에 이미지 업로드
    if not (image.content_type == 'image/jpeg' or image.content_type == 'image/jpg' or image.content_type == 'image/png'):
        raise HTTPException(status_code=400, detail="Invalid file type.")
    
    fileName = f'{datetime.now().timestamp()}.jpg'
    blob = storage.bucket().blob(f'post_images/{fileName}')
    blob.upload_from_file(image.file, content_type=image.content_type)

    url = blob.generate_signed_url(timedelta(days=365))
    user_ref.update({"image_url": url})

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
        result.append(post)
    return result


@app.get("/get_my_posts")
async def get_my_posts(user_id: str):
    doc_ref = db.collection('user').document(user_id)
    doc = doc_ref.get()
    
    if doc.exists:
        post_list = doc.to_dict()["posts"]
        my_posts = []
        
        if post_list is not None:
            # borrow_list를 30개씩 분할
            chunks = [post_list[i:i + 30] for i in range(0, len(post_list), 30)]
            for chunk in chunks:
                posts = db.collection('post').where(field_path='post_id', op_string='in', value=chunk).stream()
                for post in posts:
                    my_posts.append(post.to_dict())

        return my_posts


@app.get("/get_nearby_posts")
def get_nearby_posts(user_id: str):
    doc_ref = db.collection('user').document(user_id)
    user = doc_ref.get().to_dict()

    user_dong = user["dong"]
    location = user["location"]
    user_lat = location.latitude
    user_lng = location.longitude
    user_coords = (user_lat, user_lng)  # 사용자 위치

    nearby_posts = []  # 반경 1km 이내의 게시물을 저장

    posts_ref = db.collection('post').where('dong', '==', user_dong)
    posts = posts_ref.get()

    for post in posts:
        post_data = post.to_dict()
        post_location = post_data["map"]
        post_lat = post_location.latitude
        post_lng = post_location.longitude
        post_coords = (post_lat, post_lng)  # 포스트 위치
        print(user_coords, post_coords)
        
        distance = geodesic(user_coords, post_coords).km # 사용자 위치와 포스트 위치 간의 거리를 계산

        # 거리가 1km 이내인 경우에만 리스트에 추가
        if distance <= 1:
            nearby_posts.append(post_data)

    return nearby_posts


@app.get("/get_borrow_lend_list")
async def get_borrow_lend_list(user_id: str):
    doc_ref = db.collection('user').document(user_id)
    doc = doc_ref.get()
    
    if doc.exists:
        my_info = doc.to_dict()
        borrow_list = my_info['borrow_list']
        lend_list = my_info['lend_list']
        
        result_borrow_list = []
        result_lend_list = []

        if borrow_list is not None:
            # borrow_list를 30개씩 분할
            chunks = [borrow_list[i:i + 30] for i in range(0, len(borrow_list), 30)]
            for chunk in chunks:
                posts = db.collection('post').where(field_path='post_id', op_string='in', value=chunk).stream()
                for post in posts:
                    result_borrow_list.append(post.to_dict())
        
        if lend_list is not None:
            # lend_list를 30개씩 분할
            chunks = [lend_list[i:i + 30] for i in range(0, len(lend_list), 30)]
            for chunk in chunks:
                posts = db.collection('post').where(field_path='post_id', op_string='in', value=chunk).stream()
                for post in posts:
                    result_lend_list.append(post.to_dict())

        return {"borrow_list": result_borrow_list, "lend_list": result_lend_list}
    

@app.get("/get_chatting_room")
async def get_chatting_room(user_id: str):
    doc_ref = db.collection('user').document(user_id)
    doc = doc_ref.get()
    
    if doc.exists:
        chat_list = doc.to_dict()['chat_list']
        result_chat_list = []

        # chat_list에 neighbor_id, post_id, neighbor_nickname, neighbor_profile, last_message, last_message_time
        if chat_list is not None:
            for chat in chat_list:
                neighbor_chat_info = {}

                neighbor_id, post_id = chat.split("-")
                neighbor_chat_info['neighbor_id'] = neighbor_id
                neighbor_chat_info['post_id'] = post_id

                chatting_room = sorted([user_id, neighbor_id])
                chatting_room = ''.join(chatting_room)
                
                # neighbor 정보 저장
                neighbor = db.collection('user').document(neighbor_id).get().to_dict() # user table
                neighbor_chat_info['neighbor_nickname'] = neighbor['nickname']
                neighbor_chat_info['neighbor_profile'] = neighbor['image_url']

                # chatting 정보 저장
                collection_ref = db.collection('chats').document(chatting_room).collection('messages')
                last_doc = next(collection_ref.order_by('time', direction=firestore.Query.DESCENDING).limit(1).stream()).to_dict()
                neighbor_chat_info['last_message'] = last_doc['message']
                neighbor_chat_info['last_message_time'] = last_doc['time']
                result_chat_list.append(neighbor_chat_info)

        return result_chat_list


@app.get("/get_location")
async def get_location(location_id: str):
    doc_ref = db.collection('location').document(location_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return {"error": "Document does not exist"}


@app.post("/add_post")
async def add_post(user_id: str, post: Post):
    # 빌린 사람/빌려준 사람 초기화
    if post.borrow:
        post.borrower_user_id = user_id
        post.lender_user_id = ""
    else:
        post.lender_user_id = user_id
        post.borrower_user_id = ""

    doc_ref = db.collection('post').document()
    
    try:
        post_dict = post.dict()
        post_dict["writer_id"] = user_id
        post_dict["post_id"] = doc_ref.id
        korea = pytz.timezone('Asia/Seoul')
        now = datetime.now(korea)
        post_dict["post_time"] = now

        user = db.collection('user').document(user_id).get().to_dict() # user table
        post_dict['nickname'] = user['nickname']
        post_dict['profile'] = user['image_url']

        doc_ref.set(post_dict)

    except Exception as e:
        raise HTTPException(status_code=400, detail="An error occurred while adding the Post.")
    return post_dict


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


@app.post("/change_status")
async def change_status(post_id: str):
    try:
        doc_ref = db.collection('post').document(post_id)
        post = doc_ref.get().to_dict()
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")

        before_status = post["status"]
        if before_status == "게시":
            doc_ref.update({
                'status': '빌림중'
            })
        elif before_status == "빌림중":
            doc_ref.update({
                'status': '종료'
            })
        after_status = doc_ref.get().to_dict()["status"]
        return {"before_status": before_status, "after_status": after_status}

    except Exception as e:
        return {"error": str(e)}


@app.delete("/delete_post")
async def delete_post(post_id: str):
    doc_ref = db.collection('post').document(post_id)

    try:
        doc_ref.delete()
        return {"message": "Post has been successfully deleted."}
    except Exception as e:
        return {"message": "An error occurred while deleting post.", "exception": e}


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
            await manager.send_personal_message(f"Message text was: {message.message}", message.receiver_id)

            # Update the chat_list field in each user's document
            user_doc_A = db.collection('user').document(message.sender_id)
            user_doc_A.set({"chat_list": firestore.ArrayUnion([f"{message.receiver_id}-{message.post_id}"])}, merge=True)
            user_doc_B = db.collection('user').document(message.receiver_id)
            user_doc_B.set({"chat_list": firestore.ArrayUnion([f"{message.sender_id}-{message.post_id}"])}, merge=True)
    except WebSocketDisconnect:
        await manager.disconnect(client_id)


@app.get("/get_messages/{chat_id}")
async def get_messages(chat_id: str):
    messages = db.collection('chats').document(chat_id).collection('messages').order_by('time').stream()
    return {"messages": [doc.to_dict() for doc in messages]}


# 게시글 자동 종료
def check_end_date():
    docs = db.collection('test').get() # 모든 post 가져옴

    for doc in docs:
        post = doc.to_dict()
        end_date = post['end_date']
        status = post['status']
        now = datetime.now(pytz.timezone('Asia/Seoul'))

        # end_date가 현재 시간을 초과한 경우, status를 변경합니다.
        if end_date < now and status == "게시":
            db.collection('test').document(doc.id).update({
                'status': '종료'
            })

    print("Checking end_date...")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_end_date, "interval", minutes=1)
    scheduler.start()

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, start_scheduler)
