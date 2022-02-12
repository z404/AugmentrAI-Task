# Make a fastapi server with a mongodb database

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# get reqest
@app.get("/")
def read_root():
    return {"Hello": "World"}

