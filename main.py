from fastapi import FastAPI
# from app.views import users_view, post_view
from app.controllers import users_controller, post_controller
app = FastAPI()

app.include_router(users_controller.router)
app.include_router(post_controller.router)