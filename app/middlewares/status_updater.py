from fastapi import Request
from datetime import datetime, timedelta
from ..db.session import client
from starlette.middleware.base import BaseHTTPMiddleware

collection = 'post'

class statusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        current_time = datetime.now() + timedelta(hours=9)
        collection = client['post']
        collection.update_many(
            {"end_date": {"$lt": current_time}, "status": {"$ne": "종료"}},
            {"$set": {"status": "종료"}}
        )
        response = await call_next(request)
        return response