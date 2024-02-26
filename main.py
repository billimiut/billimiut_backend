import os, json, pytz, asyncio, io, base64
from fastapi import FastAPI, HTTPException, File, UploadFile, Body, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import HTMLResponse # websocket test를 위한 code
from pydantic import BaseModel
from firebase_admin import credentials, storage, firestore, exceptions, initialize_app, auth
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from geopy.distance import geodesic

#cred = credentials.Certificate("/mnt/c/Users/USER/billimiut/billimiut_backend/billimiut-firebase-adminsdk-cr23b-980ffebf27.json")
cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "billimiut-firebase-adminsdk-cr23b-980ffebf27.json"))
default_app = initialize_app(cred, {
    'storageBucket': 'billimiut.appspot.com'
})
db = firestore.client()


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
    emergency: Optional[bool] = None
    start_date: datetime
    end_date: datetime
    post_time: Optional[datetime] = None
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

class Edit_Post(BaseModel):
    post_id: str = ""
    title: str
    item: str
    category: str # 변경
    image_url: List[str] =[]
    money: int
    borrow: bool
    description: str
    start_date: datetime
    end_date: datetime
    female: bool
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
    borrow_money: int = 0
    lend_money: int = 0
    borrow_count: int = 0
    image_url: str = ""
    keywords : List[str] = []
    lend_count: int = 0
    locations: List[str] = []
    location: GeoPoint = GeoPoint()
    dong: str = ""
    chat_list: List[str] = []

class Nickname(BaseModel):
    user_id: str
    nickname: str

class ImageUrl(BaseModel):
    user_id: str
    image_url: str

class User_Location(BaseModel):
    user_id: str
    latitude: float
    longitude: float

# 웹소켓 연결 관리
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {} # 웹소켓 연결 관리 위한 딕셔너리, 연결된 클라이언트만 존재

    # 클라이언트가 서버에 연결됐을 때 호출
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept() # 웹소켓 연결 수락
        self.active_connections[client_id] = websocket # 클라이언트-웹소켓 새로운 연결 추가

    # 클라이언트의 연결 종료
    async def disconnect(self, client_id: str):
        websocket = self.active_connections.get(client_id)
        if websocket is not None:
            await websocket.close()
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, receiver_id: str):
        websocket = self.active_connections.get(receiver_id)
        if websocket:
            await websocket.send_text(f"Message text was: {message.message}, Time: {message.time}")

manager = ConnectionManager()

class Message(BaseModel):
    sender_id: str
    receiver_id: str
    post_id: str
    message: str
    time: str = datetime.now().isoformat()

app = FastAPI()

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
    except exceptions.FirebaseError as e:
        if e.code == 'ALREADY_EXISTS':
            return {"message": "0"}  # 이메일이 이미 사용 중인 경우
        else:
            return {"message": "1"}  # 그 외의 경우
    except Exception:  # 그 외의 모든 예외를 처리합니다.
        return {"message": "1"}
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
    user_ref.update({
        'location': firestore.GeoPoint(location_data.latitude, location_data.longitude)
    })
    
    return {"message": "Location successfully added"}

#ok
@app.post("/my_info")
async def my_info(user: Login_Token = Body(...)):
    user_id = user.login_token
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
async def add_post(
    user_id: str = Form(...),
    title: str = Form(...),
    item: str = Form(...),
    category: str = Form(...),
    money: int = Form(...),
    borrow: bool = Form(...),
    description: str = Form(...),
    start_date: datetime = Form(...),
    end_date: datetime = Form(...),
    female: bool = Form(...),
    address: str = Form(""),
    detail_address: str = Form(""),
    name: str = Form(""),
    map_latitude: float = Form(0),
    map_longitude: float = Form(0),
    dong: str = Form(""),
    images: List[UploadFile] = File(None),
):
    doc_ref = db.collection('post').document()

    print(type(images))
    # upload images to firebase storage
    urls = []
    blobs = []
    if images is not None:
        for image in images:
            if image.content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
                raise HTTPException(status_code=400, detail="Invalid file type.")
            
            fileName = f'{datetime.now().timestamp()}.jpg'
            blob = storage.bucket().blob(f'post_images/{fileName}')
            blob.upload_from_file(image.file, content_type=image.content_type)

            url = blob.generate_signed_url(timedelta(days=365))
            urls.append(url)
            blobs.append(blob)
            
            print(f"Image {fileName} uploaded successfully.")

    now = datetime.now(timezone.utc)
    emergency = True if start_date - now <= timedelta(minutes=30) else False
    post_id = doc_ref.id

    try:
        user_ref = db.collection('user').document(user_id)
        user = user_ref.get().to_dict() # user table
        if user is None:
            raise ValueError("User does not exist.")

        # Create the post dictionary manually
        post_dict = {
            "post_id": post_id,
            "writer_id": user_id,
            "title": title,
            "item": item,
            "category": category,
            "money": money,
            "borrow": borrow,
            "description": description,
            "emergency": emergency,
            "start_date": start_date,
            "end_date": end_date,
            "post_time": now,
            "female": female,
            "status": "게시",
            "borrower_user_id": "",
            "lender_user_id": "",
            "nickname": user['nickname'],
            "profile": user['image_url'],
            "address": address,
            "detail_address": detail_address,
            "name": name,
            "map": {"latitude": map_latitude, "longitude": map_longitude},
            "dong": dong,
            "image_url": urls,
        }

        user_ref.update({'posts': firestore.ArrayUnion([post_id])})
        doc_ref.set(post_dict)

    except ValueError as ve:
        for blob in blobs:
            blob.delete()
            print(f"Image {fileName} deleted successfully.")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        for blob in blobs:
            blob.delete()
            print(f"Image {fileName} deleted successfully.")
        raise HTTPException(status_code=500, detail=f"An error occurred while adding the Post: {str(e)}")
    return post_dict


@app.put("/edit_post")
async def edit_post(
    post_id: str = Form(...),
    title: str = Form(...),
    item: str = Form(...),
    category: str = Form(...),
    money: int = Form(...),
    borrow: bool = Form(...),
    description: str = Form(...),
    start_date: datetime = Form(...),
    end_date: datetime = Form(...),
    female: bool = Form(...),
    address: str = Form(""),
    detail_address: str = Form(""),
    name: str = Form(""),
    map_latitude: float = Form(0),
    map_longitude: float = Form(0),
    dong: str = Form(""),
    images: List[UploadFile] = File(None),
):
    doc_ref = db.collection('post').document(post_id)
    
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Post does not exist")
    
    urls = []
    blobs = []
    try:
        if images is not None:
            for image in images:
                if image.content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
                    raise HTTPException(status_code=400, detail="Invalid file type.")
                
                fileName = f'{datetime.now().timestamp()}.jpg'
                blob = storage.bucket().blob(f'post_images/{fileName}')
                blob.upload_from_file(image.file, content_type=image.content_type)

                url = blob.generate_signed_url(timedelta(days=365))
                urls.append(url)
                blobs.append(blob)
                
                print(f"Image {fileName} uploaded successfully.")
        
        now = datetime.now(timezone.utc)
        emergency = True if start_date - now <= timedelta(minutes=30) else False
        
        doc_ref.update({
            "title": title,
            "item": item,
            "category": category,
            "money": money,
            "borrow": borrow,
            "description": description,
            "emergency": emergency,
            "start_date": start_date,
            "end_date": end_date,
            "female": female,
            "address": address,
            "detail_address": detail_address,
            "name": name,
            "map": {"latitude": map_latitude, "longitude": map_longitude},
            "dong": dong,
            "image_url": urls,
        })
        
        return doc_ref.get().to_dict()
    
    except Exception as e:
        for blob in blobs:
            blob.delete()
            print(f"Image {fileName} deleted successfully.")
        raise HTTPException(status_code=500, detail="An error occurred while updating the post")
    

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
async def change_status(post_id: str, borrower_user_id: str, lender_user_id: str):
    try:
        doc_ref = db.collection('post').document(post_id)
        post = doc_ref.get().to_dict()
        money = post["money"]

        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")

        before_status = post["status"]
        if before_status == "게시":
            borrower_ref = db.collection('user').document(borrower_user_id)
            lender_ref = db.collection('user').document(lender_user_id)

            doc_ref.update({
                'status': '빌림중',
                'borrower_user_id': borrower_user_id,
                'lender_user_id': lender_user_id
            })
            
            borrower_ref.update({
                'borrow_count': firestore.Increment(1),
                'borrow_list': firestore.ArrayUnion([post_id]),
                'borrow_money': firestore.Increment(money)
            })
            lender_ref.update({
                'lend_count': firestore.Increment(1),
                'lend_list': firestore.ArrayUnion([post_id]),
                'lend_money': firestore.Increment(money)
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
    post = doc_ref.get().to_dict()
    writer_id = post["writer_id"]

    if post["status"] == "게시":
        user_ref = db.collection('user').document(writer_id)
        user_ref.update({'posts': firestore.ArrayRemove([post_id])})
    else: # 빌림중/종료
        borrower_id = post["borrower_user_id"]
        lender_id = post["lender_user_id"]
        borrower_ref = db.collection('user').document(borrower_id)
        lender_ref = db.collection('user').document(lender_id)

        if writer_id == borrower_id: # 글 작성자가 빌린사람
            borrower_ref.update({'posts': firestore.ArrayRemove([post_id])})
        else: # 글 작성자가 빌려준 사람
            lender_ref.update({'posts': firestore.ArrayRemove([post_id])})

        borrower_ref.update({'borrow_list': firestore.ArrayRemove([post_id])})
        lender_ref.update({'lend_list': firestore.ArrayRemove([post_id])})

    try:
        doc_ref.delete()
        return {"message": "Post has been successfully deleted."}
    except Exception as e:
        return {"message": "An error occurred while deleting post.", "exception": e}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id) # sender 웹소켓 연결
    try:
        while True:
            data = await websocket.receive_text() # sender가 보낸 메시지
            data_json = json.loads(data) # 메시지를 json으로 파싱
            message = Message(**data_json, time = datetime.now().isoformat())
            chat_id = ''.join(sorted([message.sender_id, message.receiver_id]))
            print(f"Message content: {message.dict()}")
            #db.collection('chats').document(chat_id).collection('messages').add(message.dict())
            # sender가 보낸 메시지를 서버가 받고, 서버가 이를 receiver에게 전달
            await manager.send_personal_message(f"Message text was: {message.message}", message.receiver_id)

            # Update the chat_list field in each user's document
            #user_doc_A = db.collection('user').document(message.sender_id)
            #user_doc_A.set({"chat_list": firestore.ArrayUnion([f"{message.receiver_id}-{message.post_id}"])}, merge=True)
            #user_doc_B = db.collection('user').document(message.receiver_id)
            #user_doc_B.set({"chat_list": firestore.ArrayUnion([f"{message.sender_id}-{message.post_id}"])}, merge=True)
    except WebSocketDisconnect:
        await manager.disconnect(client_id)


@app.get("/get_messages/{chat_id}")
async def get_messages(chat_id: str):
    messages = db.collection('chats').document(chat_id).collection('messages').order_by('time').stream()
    return {"messages": [doc.to_dict() for doc in messages]}


# 게시글 자동 종료
def check_end_date():
    docs = db.collection('post').get() # 모든 post 가져옴

    for doc in docs:
        post = doc.to_dict()
        end_date = post['end_date']
        status = post['status']
        now = datetime.now(pytz.timezone('Asia/Seoul'))

        # end_date가 현재 시간을 초과한 경우, status를 변경합니다.
        if end_date < now and status == "게시":
            db.collection('post').document(doc.id).update({
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