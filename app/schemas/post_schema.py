from typing import Optional, List
from pydantic import BaseModel, Field

class PostBase(BaseModel):
    address: Optional[str]
    detail_address: Optional[str]
    dong: Optional[str]
    borrow: Optional[bool]
    borrower_uuid: Optional[str]
    category: Optional[str]
    title: Optional[str]
    description: Optional[str]
    emergency : Optional[bool]
    start_date: Optional[str]
    end_date: Optional[str]
    female: Optional[bool]
    image_url: Optional[str]
    item: Optional[str]
    lender_uuid: Optional[str]
    map_coordinates: Optional[List[dict[str, float]]]
    # map_coordinates: Optional[List[str:float]]
    price: Optional[int]    
    # post_uuid: Optional[str] # post_uuid를 _id로 대체 
    post_time: Optional[str]
    status: Optional[str]

class PostUpdate(BaseModel):
    post_uuid: str
    borrower_uuid: str
    lender_uuid: str
