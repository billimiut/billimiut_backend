import datetime

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.log_util import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"{datetime.datetime.now()} Request {request.method} {request.url}")

        response = await call_next(request)

        # 응답 정보 및 처리 시간 로깅
        logger.info(f"{datetime.datetime.now()} Response to {request.method} {request.url} Status {response.status_code}")

        return response
