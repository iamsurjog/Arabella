from types import new_class
from fastapi import FastAPI
from fastapi.routing import request_response
from pydantic import BaseModel

app = FastAPI()

class Graph(BaseModel):
    session_id: str

class Query(BaseModel):
    session_id: str
    query: str
    new_session: bool | None = True

@app.post("/query")
async def query(query:Query):
    return f"{query.session_id  = }, {query.query  = }, {query.new_session  = }"

## TODO: Do we even need this?
@app.get("/answer")
async def answer():
    pass

@app.post("/graph")
async def graph(graph:Graph):
    return f"{graph.session_id = }"
