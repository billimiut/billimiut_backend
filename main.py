from fastapi import FastAPI
from app.views import users_view

app = FastAPI()

app.include_router(users_view.router)