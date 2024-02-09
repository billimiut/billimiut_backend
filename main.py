import os
from fastapi import FastAPI, HTTPException, File, UploadFile, Body
from pydantic import BaseModel
from firebase_admin import credentials, storage, firestore, exceptions, initialize_app, auth
from typing import List, Optional
from datetime import datetime

#cred = credentials.Certificate("/mnt/c/Users/USER/billimiut/billimiut_backend/billimiut-firebase-adminsdk-cr23b-980ffebf27.json")
cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), "billimiut-firebase-adminsdk-cr23b-980ffebf27.json"))
default_app = initialize_app(cred, {
    'storageBucket': 'billimiut.appspot.com'
})
db = firestore.client()

class GeoPoint(BaseModel):
    latitude: float
    longitude: float

# category_id <- 일단 category: str으로 대체
class Post(BaseModel):
    post_id: str = ""
    nickname: str
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
    map: GeoPoint
    address: str
    detail_address: str
    dong: str

class Add_Post(BaseModel):
    user_id: str
    post: Post
    location: Location

app = FastAPI()

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

#ok
@app.get("/get_posts")
async def read_posts():
    print("get_posts")
    docs = db.collection('post').stream()
    result = []
    for doc in docs:
        data = doc.to_dict()
        selected_fields = {field: data.get(field, None) for field in ['post_id', 'nickname', 'title', 'description', 'item', 'image_url', 'money', 'borrow', 'description', 'emergency', 'start_date', 'end_date', 'location_id', 'female', 'status', 'category_id', 'borrower_user_id', 'lender_user_id']}
        result.append(selected_fields)
    return result


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
        print(image.content_type)
        if not (image.content_type == 'image/jpeg' or image.content_type == 'image/jpg' or image.content_type == 'image/png'):
            raise HTTPException(status_code=400, detail="Invalid file type.")
        
        fileName = f'{datetime.now().timestamp()}.jpg'
        blob = storage.bucket().blob(f'post_images/{fileName}')

        blob.upload_from_file(image.file, content_type=image.content_type)

        downloadUrl = blob.public_url
        urls.append(downloadUrl)

    return {"urls": urls}