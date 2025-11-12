from fastapi import FastAPI
from pydantic import BaseModel
import uuid
import os
from dotenv import load_dotenv
from crawler import crawl_relations
from query_bridge import QueryBridge
from rag import GraphRAG

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize modules with environment configuration
query_bridge = QueryBridge()
rag = GraphRAG(
    embedding_model=os.getenv('EMBEDDING_MODEL', 'nomic-embed-text:v1.5'),
    language_model=os.getenv('LANGUAGE_MODEL', 'llama3.2:3b'),
    vector_size=int(os.getenv('VECTOR_SIZE', '768')),
    kuzu_db_path=os.getenv('KUZU_DB_PATH', './kuzu_db'),kuzu
    qdrant_path=os.getenv('VECTOR_DB_PATH', './vector_db'),
    ollama_host=os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
)


class Graph(BaseModel):
    session_id: str


class Query(BaseModel):
    session_id: str = ""
    query: str
    new_session: bool | None = True


@app.post("/query")
async def post_query(q: Query):
    """
    Main query endpoint
    
    Flow:
    1. Generate/use session ID
    2. Transform query via Query Bridge
    3. Crawl web for results
    4. Index in Graph-RAG
    5. Generate answer
    6. Return response
    """
    try:
        # Step 1: Session management
        session_id = str(uuid.uuid4()) if q.new_session else q.session_id
        
        # Step 2: Transform query (Query Bridge)
        search_query = query_bridge.transform(q.query)
        print(f"Transformed query: {search_query}")
        
        # Step 3: Crawl web (Crawler module)
        link_text_map, relations = crawl_relations(search_query, max_depth=2)
        print(f"Crawled {len(link_text_map)} pages with {len(relations)} relationships")
        
        # Step 4: Index in Graph-RAG
        success = rag.bulk_index_from_crawler(relations, link_text_map, session_id)
        if not success:
            return {"error": "Failed to index documents", "session_id": session_id}
        
        # Step 5: Generate answer
        answer = rag.answer(q.query, session_id)
        
        # Step 6: Return
        return {
            "session_id": session_id,
            "query": q.query,
            "search_query": search_query,
            "answer": answer,
            "documents_indexed": len(link_text_map),
            "relationships": len(relations)
        }
    
    except Exception as e:
        return {"error": str(e), "session_id": q.session_id}


@app.get("/answer")
async def answer():
    return {"status": "not implemented"}


@app.post("/graph")
async def graph(graph: Graph):
    """Get graph information for a session"""
    try:
        nodes = rag.graph_db.get_session_nodes(graph.session_id)
        edges = rag.graph_db.get_session_edges(graph.session_id)
        return {
            "session_id": graph.session_id,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes)
        }
    except Exception as e:
        return {"error": str(e), "session_id": graph.session_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
