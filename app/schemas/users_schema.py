from pydantic import BaseModel

class User(BaseModel):
    id: str
    pw: str
    nickname: str

    class Config:
        schema_extra = {
            "example": {
                "id": "test_id",
                "pw": "test_pw",
                "nickname": "test_nickname"
            }
        }