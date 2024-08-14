from fastapi import FastAPI
from app.controllers import users_controller, post_controller, chat_controller
from app.middlewares.logger import LoggingMiddleware
from app.middlewares.status_updater import statusMiddleware

app = FastAPI()

app.include_router(users_controller.router)
app.include_router(post_controller.router)
app.include_router(chat_controller.router)

app.add_middleware(LoggingMiddleware)
app.add_middleware(statusMiddleware)