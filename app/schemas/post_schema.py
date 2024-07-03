from datetime import timedelta, timezone, datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from fastapi import File, UploadFile

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
    item: Optional[str]
    lender_uuid: Optional[str]
    map_coordinates: Optional[List[Dict[str, float]]]
    price: Optional[int]
    post_time: Optional[datetime]
    status: Optional[str]  
    image_file: Optional[UploadFile] = File(...)
