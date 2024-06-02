from typing import Optional, List, Dict
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
    emergency: Optional[bool]
    start_date: Optional[str]  # 나중에 datetime으로 변경
    end_date: Optional[str]  # 나중에 datetime으로 변경
    female: Optional[bool]
    image_url: Optional[str]
    item: Optional[str]
    lender_uuid: Optional[str]
    map_coordinates: Optional[List[Dict[str, float]]]
    price: Optional[int]
    post_time: Optional[str]  # 나중에 datetime으로 변경
    status: Optional[str]

class PostUpdate(BaseModel):
    post_uuid: str
    borrower_uuid: str
    lender_uuid: str
