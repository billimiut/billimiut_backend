from fastapi import APIRouter, HTTPException, Body
from app.schemas.post_schema import PostBase, PostUpdate
from app.controllers.post_controller import create_post, get_post, get_posts, put_post_status, delete_post, get_posts_by_user, get_posts_by_user_and_status, update_post

router = APIRouter()

@router.post("/post")
async def create_post_route(post: PostBase = Body(...)):
    return await create_post(post)

@router.get("/post/{post_id}")
async def get_post_route(post_id: str):
    return await get_post(post_id)

@router.get("/post")
async def get_posts_route():
    return await get_posts()

@router.put("/post/status")
async def put_post_status_route(post: PostUpdate = Body(...)):
    return await put_post_status(post)

@router.delete("/post/{post_id}")
async def delete_post_route(post_id: str):
    return await delete_post(post_id)

@router.get("/post/{user_id}")
async def get_posts_by_user_route(user_id: str):
    return await get_posts_by_user(user_id)

@router.get("/post/{user_id}?status={status}")
async def get_posts_by_user_id_and_status_route(user_id: str, status: str):
    return await get_posts_by_user_and_status(user_id, status)

@router.put("/post/{post_id}")
async def put_post_by_post_id_route(post_id: str, post: PostBase = Body(...)):
    return await put_post_by_post_id_route(post_id, post)

## deprecated ##
## 나중에 이전 API들 연결해주는 그런걸로 사용할 수 있을 듯 ##