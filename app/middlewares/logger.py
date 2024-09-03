import datetime

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.log_util import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        logger.info(f"{datetime.datetime.now()} Request {request.method} {request.url}")
        # 요청이 들어온 경우 request를 로깅한다. 시각, method, request uri를 로깅한다.
        
        body = await request.body()
        if body:
            logger.info(f"Request Body:")
            logger.info(body.decode('utf-8'))
            
        response = await call_next(request)
        # 서비스 내에서 request가 처리되고 나면 response가 온다.

        response = await call_next(request)
        response_body = b""
        async for chunk in response.body:
            response_body += chunk
        logger.info(f"Response Body:")
        logger.info(response_body.decode('utf-8'))

        logger.info(f"{datetime.datetime.now()} Response to {request.method} {request.url} Status {response.status_code}")
        # 요청이 들어온 경우 response를 로깅한다. 시각, 어떤 요청에 대한 응답인지, 상태코드를 로깅한다.

        return response
