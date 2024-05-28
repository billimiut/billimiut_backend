from typing import Optional, List
from pydantic import BaseModel, Field

class UserBase(BaseModel):
    borrow_list: Optional[List[str]]
    chat_list: Optional[List[str]]
    id: Optional[str]
    profile_image: Optional[str]
    keywords: Optional[List[str]]
    lend_list: Optional[List[str]]
    nickname: Optional[str]
    posts: Optional[List[str]]
    pw: Optional[str]
    salt: Optional[str]
    login_type: Optional[str]

class UserCreate(BaseModel):
    id: str
    pw: str
    nickname: str

class UserLogin(BaseModel):
    id: str
    pw: str

class UserGetInfo(BaseModel):
    id: str

class UserUpdate(BaseModel):
    id: str
    nickname: str