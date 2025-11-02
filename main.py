from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Query(BaseModel):
    query: str

class Context(BaseModel):
    # dummy value
    something: str

@app.get("/query")
async def query(query:Query):
    pass

@app.get("/answer")
async def answer():
    pass

@app.get("/expand")
async def expand(context:Context):
    pass

@app.get("/graph")
async def graph():
    pass

