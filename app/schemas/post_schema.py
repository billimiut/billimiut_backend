from datetime import timedelta, timezone, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from fastapi import File, UploadFile, Form

class PostBase(BaseModel):
    address: Optional[str]
    detail_address: Optional[str]
    dong: Optional[str]
    borrow: Optional[bool]
    borrower_uuid: Optional[str]
    category: Optional[str]
    title: Optional[str]
    description: Optional[str]
    emergency: Optional[bool]
    start_date: Optional[datetime]
    end_date: Optional[datetime] 
    female: Optional[bool]
    image_url: Optional[str]
    item: Optional[str]
    lender_uuid: Optional[str]
    map_coordinates: Optional[List[Dict[str, float]]]
    price: Optional[int]
    post_time: Optional[datetime]
    status: Optional[str]

class PostUpdate(BaseModel):
    post_id: str
    borrower_uuid: str
    lender_uuid: str

class PostMake(BaseModel):
    address: str = Form(...)
    detail_address: str = Form(...)
    dong: str = Form(...)
    borrow: bool = Form(...)
    borrower_uuid: Optional[str] = Form(None)
    category: str = Form(...)
    title: str = Form(...)
    description: str = Form(...)
    emergency: bool = Form(...)
    start_date: datetime = Form(...)
    end_date: datetime = Form(...)
    female: bool = Form(...)
    item: str = Form(...)
    lender_uuid: Optional[str] = Form(None)
    map_coordinates: List[Dict[str, float]] = Form(...)
    price: int = Form(...)
    post_time: datetime = Form(...)
    status: str = Form(...)
