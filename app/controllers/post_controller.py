from fastapi import HTTPException, APIRouter, HTTPException, Body
from app.schemas.post_schema import PostBase, PostUpdate
from app.models.post_models import insert_post, find_post, find_posts, update_post_status, erase_post, find_posts_by_user, find_posts_by_user_and_status, update_post

router = APIRouter()

@router.post("/post")
async def create_post(post: PostBase):
    try:
        # 중복여부 확인 필요
        res = insert_post(post)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Create post failed")
    
@router.get("/post/{post_id}")
async def get_post(post_id: str):
    try:
        res = find_post(post_id)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Get post failed")

@router.get("/post")
async def get_post():
    try:
        res = find_posts()
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Get posts failed")

@router.put("/post/status")
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

@router.get("/post/{user_id}")
async def get_posts_by_user(user_id: str):
    try:
        res = find_posts_by_user(user_id)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Get posts by user failed")
    
@router.get("/post/{user_id}?status={status}")
async def get_posts_by_user_and_status(user_id: str, status: str):
    try:
        res = find_posts_by_user_and_status(user_id, status)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Get posts by user and status failed")

@router.put("/post/{post_id}")
async def put_post_by_post_id(post_id: str, post: PostBase):
    try:
        res = update_post(post_id, post)
        return res
    except Exception:
        return HTTPException(status_code=400, detail="Update post failed")