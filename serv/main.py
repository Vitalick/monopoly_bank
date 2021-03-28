from fastapi import FastAPI, Depends

from pydantic2ts import generate_typescript_defs

from . import controllers
from .dependencies import get_query_token

generate_typescript_defs("./serv/models.py", "./src/api.ts")

app = FastAPI()

app.include_router(controllers.router)

# @app.get("/")
# async def root():
#     return {"message": "Hello Bigger Applications!"}