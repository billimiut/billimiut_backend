import json
import traceback
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import ValidationError

from app.middlewares.images import upload_image
from app.models.post_models import insert_post, find_post, find_posts, update_post_status, erase_post, find_posts_by_user, update_post, edit_post_image_url, report_post
from app.models.users_models import find_user_by_id
from app.models.users_models import update_user_post
from app.schemas.post_schema import PostBase, PostUpdate
from app.schemas.users_schema import UserGetInfo
from geopy.distance import geodesic
router = APIRouter()


@router.post("/post")
# 기존에 postMake를 사용하여 schema를 받아오려 하였으나, 해당 과정에서 entity 에러가 계속 떠서 Form으로 수정했음. 이 과정도 수정이 필요할 듯 함.
async def create_post(post: str = Form(...), image_file: List[UploadFile] = File(None)):
    try:
        image_urls = []
        if image_file:        
            for single_file in image_file:
                filename = await upload_image(single_file)
                image_urls.append(filename)
        post_dict = json.loads(post)
        post_dict['image_url'] = image_urls
        post = PostBase(**post_dict)
        res = insert_post(post)
        post_dict["post_id"] = str(res)
        if post_dict['borrow']:
            post_dict["writer_uuid"] = post_dict['borrower_uuid']
        else:
            post_dict["writer_uuid"] = post_dict['lender_uuid']
        writer_uuid = post_dict["writer_uuid"]
        update_user_post(writer_uuid, post_dict["post_id"])
        writer_info, message = find_user_by_id(UserGetInfo(id=writer_uuid))
        post_dict["nickname"] = writer_info["nickname"]        
        return post_dict
    except Exception:
        return HTTPException(status_code=400, detail="Create post failed")


@router.get("/post/{post_id}")
async def get_post(post_id: str):
    try:
        res = find_post(post_id)
        if res['borrow']:
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
        print(res)
        for post in res:
            if post['borrow']:
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


@router.put("/post/status") # 이거 굳이 borrower uuid랑 lender uuid를 받아올 필요가 없는거 같음. post_id만 받아오면 될듯
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


@router.put("/post/{post_id}")
async def put_post_by_post_id(post_id: str, post: str = Form(...), add_image: List[UploadFile] = File(None)):
    try:
        print("edit post start with the post_id", post_id)
        post_dict = json.loads(post)
        print(post_dict)

        image_urls = []
        remove_image_url = []
        if 'remove_image_url' in post_dict and post_dict['remove_image_url']:
            remove_image_url = post_dict['remove_image_url']
            del post_dict['remove_image_url']

        res = edit_post_image_url(post_id, remove_image_url)
        if 'error' in res:
            raise HTTPException(status_code=400, detail=res['error'])

        if add_image:
            for single_file in add_image:
                filename = await upload_image(single_file)
                image_urls.append(filename)

        image_urls += res

        post_dict['image_url'] = image_urls
        print(post_dict)
        
        try:
            post_model = PostBase(**post_dict)
        except ValidationError as e:
            print("Validation error:", e)
            raise HTTPException(status_code=422, detail="Validation error in post data")

        print(post_model)
        res = update_post(post_id, post_model) # res에 post_dict값과 똑같은 값이 담김
        if post_dict.get('borrow'):
            post_dict["writer_id"] = post_dict['borrower_uuid']
        else:
            post_dict["writer_id"] = post_dict['lender_uuid']
        post_dict["post_id"] = post_id
        return post_dict
    except HTTPException as e:
        return e
    except Exception as e:
        print(e)
        return HTTPException(status_code=400, detail="Update post failed")

@router.post("/post/report/{post_id}")
async def post_report_post(post_id: str, reporter_uuid: str, report_reason: str):
    try:
        res = report_post(post_id, reporter_uuid, report_reason)
        return res["message"] # 현재는 어떤 결과가 나왔다라고만 이렇게 리턴을 하는데, 이거는 추후 변경하는게 좋을 것 같음.
    except Exception as e:
        print(e)
        return HTTPException(status_code=400, detail="Report post failed")
