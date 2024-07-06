import traceback
from typing import Optional,List
from fastapi import HTTPException, APIRouter, HTTPException, Body, UploadFile, File,Form,Depends
from app.models.users_models import find_user_by_id
from app.schemas.post_schema import PostBase, PostUpdate, PostMake
from app.models.post_models import insert_post, find_post, find_posts, update_post_status, erase_post, find_posts_by_user, find_posts_by_user_and_status, update_post
import os,json
from app.schemas.users_schema import UserGetInfo
from app.middlewares.images import upload_image
from app.models.users_models import find_user_by_id
router = APIRouter()

@router.post("/post")
async def create_post(post: str = Form(...), image_file: List[UploadFile] = File(...)):
    try:
        image_urls = []        
        for single_file in image_file:
            filename = await upload_image(single_file)
            image_urls.append(filename)
        post_dict = json.loads(post)
        post_dict['image_url'] = image_urls
        post = PostBase(**post_dict)
        res = insert_post(post)
        print(str(res))
        post_dict["post_id"] = str(res)
        if(post_dict['borrow'] == True):
            post_dict["writer_uuid"] = post_dict['borrower_uuid']
        else:
            post_dict["writer_uuid"] = post_dict['lender_uuid']
        print(post_dict["writer_uuid"])
        writer_info, message = find_user_by_id(UserGetInfo(id=post_dict["writer_uuid"]))
        print(writer_info["nickname"])
        post_dict["nickname"] = writer_info["nickname"]        
        return post_dict
    except Exception:        
        return HTTPException(status_code=400, detail="Create post failed")
    
@router.get("/post/{post_id}")
async def get_post(post_id: str):
    try:
        res = find_post(post_id)
        if(res['borrow'] == True):
            writer_uuid = res['borrower_uuid']
        else:
            writer_uuid = res['lender_uuid']
        writer_info, message = find_user_by_id(UserGetInfo(id=writer_uuid))
        res['nickname'] = writer_info['nickname']
        res['profile_image'] = writer_info['profile_image']
        res['writer_uuid'] = writer_uuid
        post_id = res['_id']
        del res['_id']
        res['post_id'] = post_id
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Get post failed")

@router.get("/post")
async def get_post():
    try:
        res = find_posts()
        for post in res:
            if(post['borrow'] == True):
                writer_uuid = post['borrower_uuid']
            else:
                writer_uuid = post['lender_uuid'] 
            writer_info, message = find_user_by_id(UserGetInfo(id=writer_uuid))
            post['nickname'] = writer_info['nickname']
            post['profile_image'] = writer_info['profile_image']
            post['writer_uuid'] = writer_uuid
            post_id = post['_id']
            del post['_id']
            post['post_id'] = post_id
        return res
    except Exception as e:
        traceback.print_exc()
        print(e)
        return HTTPException(status_code=400, detail="Get posts failed")

@router.put("/post/status") ## 이거 굳이 borrower uuid랑 lender uuid를 받아올 필요가 없는거 같음. post_id만 받아오면 될듯
async def put_post_status(post: PostUpdate):
    try:
        res = update_post_status(post)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Update post status failed")

@router.delete("/post/{post_id}")
async def delete_post(post_id: str):
    try:
        res = erase_post(post_id)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Delete post failed")

@router.get("/post/personal/{user_id}")
async def get_posts_by_user(user_id: str, status: Optional[str] = None):
    try:
        writer_info, message = find_user_by_id(UserGetInfo(id=user_id))
        res = find_posts_by_user(user_id)
        for post in res:
            post['_id'] = str(post['_id'])
            post['nickname'] = writer_info['nickname']
            post['profile_image'] = writer_info['profile_image']
            print(user_id)
            post['writer_uuid'] = user_id
            post_id = post['_id']
            del post['_id']
            post['post_id'] = post_id

        if status:
            # 일단 서버 자체적으로 구현
            for post in res:
                if post['status'] != status:
                    res.remove(post)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Get posts by user failed")
    
# @router.get("/post/personal/{user_id}?status={status}")
# async def get_posts_by_user_and_status(user_id: str, status: str):
#     print(status)
#     try:
#         res = find_posts_by_user_and_status(user_id, status)
#         return res
#     except Exception:
#         return HTTPException(status_code=400, detail="Get posts by user and status failed")

@router.put("/post/{post_id}")
async def put_post_by_post_id(post_id:str, post: str = Form(...), image_file: List[UploadFile] = File(...)):
    try:
        image_urls = []
        for single_file in image_file:
            filename = await upload_image(single_file)
            image_urls.append(filename)
        post_dict = json.loads(post)
        post_dict['image_url'] = image_urls        
        post = PostBase(**post_dict)
        res = update_post(post_id, post)
        if(post_dict['borrow'] == True):
            post_dict["writer_id"] = post_dict['borrower_uuid']
        else:
            post_dict["writer_id"] = post_dict['lender_uuid']
        return res, post_dict
    except Exception:
        return HTTPException(status_code=400, detail="Update post failed")
    
# @router.post("/post/upload_image")
# async def upload_image_test(file: UploadFile = File(...)):
#     try:
#         filename = await upload_image(file)
#         # post_dict = json.loads(post)
#         # print(post_dict)
#         return {"filename": filename}
#         # else:
#         #     return HTTPException(status_code=400, detail="Upload image failed")
#         # 이미지를 서버(리눅스)에 저장하는 코드.
#         # post_dict = json.loads(post)
#         # post = PostBase(**post_dict)
#         # post_id = post.borrower_uuid if post.borrower_uuid else post.lender_uuid
#         # res = find_post(post_id)
#         # if res:
#         #     current_dir = os.path.dirname(os.path.realpath(__file__)) 
#         #     UPLOAD_DIR = os.path.join(current_dir, "../images")
#         #     content = await file.read()
#         #     filename = f"{post_id}.png"
#         #     with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
#         #         f.write(content)
#         #     return {"filename": filename, "post_id": post_id, "status": "success"}
#     except Exception:
#         return HTTPException(status_code=400, detail="Upload image failed")