from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Query(BaseModel):
    query: str

@app.get("/query")
async def query(query:Query):
    pass

@app.get("/answer")
async def answer():
    pass

@app.get("/graph")
async def graph():
    pass

