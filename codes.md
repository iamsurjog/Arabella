# Project Code

This file contains all the code for the project, organized by file path.

---
**File:** `/home/randomguy/surjo/projs/arabella/.gitignore`
```
.venv/
__pycache__/
.env
```
---
**File:** `/home/randomguy/surjo/projs/arabella/config.yaml`
```yaml
embeddings-model: nomic-embed-text:v1.5
language-model : 'llama3.2:3b'
```
---
**File:** `/home/randomguy/surjo/projs/arabella/crawler/__init__.py`
```python
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_plain_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]): tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return text

def extract_links(base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        url = urljoin(base_url, href)
        if urlparse(url).scheme in ["http", "https"]:
            links.add(url)
    return links

def crawl_relations(url, max_depth=2):
    visited = set()
    link_text_map = dict()
    relations = []

    def _crawl(current_url, depth, parent=None):
        if depth > max_depth or current_url in visited:
            return
        try:
            resp = requests.get(current_url, timeout=10)
            resp.raise_for_status()
            html = resp.text
            plain_text = get_plain_text(html)
            link_text_map[current_url] = plain_text
            visited.add(current_url)
            if parent is not None:
                relations.append((parent, current_url))
            if depth < max_depth:
                links = extract_links(current_url, html)
                for link in links:
                    _crawl(link, depth + 1, current_url)
        except Exception:
            pass  # skip broken

    _crawl(url, 0, None)
    return [link_text_map, relations]

# Usage:
if __name__ == "__main__":
    start_url = "http://127.0.0.1:5000"
    results = crawl_relations(start_url, max_depth=2)
    # Output: [{'link1': 'text1', ...}, [(link1, link2), ...]]
    print(results)
```
---
**File:** `/home/randomguy/surjo/projs/arabella/db/KuzuDB.py`
```python
import kuzu
from typing import List, Optional, Dict, Any

class KuzuDB:
    def __init__(self, db_path: str):
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._init_schema()

    def _init_schema(self):
        """Initialize graph schema if not exists"""
        try:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    link STRING PRIMARY KEY,
                    session_id STRING,
                    title STRING,
                    summary STRING,
                    embedding_id STRING
                )
            """)
            
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS hyprlink (
                    FROM links TO links,
                    session_id STRING
                )
            """)
        except Exception as e:
            print(f"Schema init info: {e}")

    def show(self, query: str) -> List:
        """Execute query and return results"""
        try:
            result = self.conn.execute(query)
            return list(result)
        except Exception as e:
            print(f"Query error: {e}")
            return []

    def insert_rel(self, link1: str, link2: str, session_id: str):
        """Insert relationship between two links"""
        try:
            link1_safe = self._escape(link1)
            link2_safe = self._escape(link2)
            session_safe = self._escape(session_id)
            
            query = f"""
                MATCH (l1:links {{link:'{link1_safe}', session_id:'{session_safe}'}}),
                      (l2:links {{link:'{link2_safe}', session_id:'{session_safe}'}})
                CREATE (l1)-[:hyprlink {{session_id:'{session_safe}'}}]->(l2)
            """
            self.conn.execute(query)
        except Exception as e:
            print(f"Insert relationship error: {e}")

    def insert_node(self, link: str, session_id: str):
        """Insert node into graph"""
        try:
            link_safe = self._escape(link)
            session_safe = self._escape(session_id)
            
            query = f"""
                CREATE (n:links {{
                    link:'{link_safe}',
                    session_id:'{session_safe}',
                    title:'',
                    summary:'',
                    embedding_id:''
                }})
            """
            self.conn.execute(query)
        except Exception as e:
            print(f"Insert node error: {e}")

    def get_neighbors(self, link: str, session_id: str, depth: int = 1) -> List[str]:
        """Get connected nodes within specified depth"""
        try:
            link_safe = self._escape(link)
            session_safe = self._escape(session_id)
            
            query = f"""
                MATCH (start:links {{link:'{link_safe}', session_id:'{session_safe}'}})
                       -[:hyprlink*1..{depth}]->
                       (neighbor:links {{session_id:'{session_safe}'}})
                RETURN neighbor.link
            """
            results = self.show(query)
            return [r[0] if isinstance(r, (list, tuple)) else r.get('neighbor.link', '') for r in results]
        except Exception as e:
            print(f"Get neighbors error: {e}")
            return []

    def get_session_nodes(self, session_id: str) -> List[str]:
        """Get all nodes in a session"""
        try:
            session_safe = self._escape(session_id)
            query = f"MATCH (n:links {{session_id:'{session_safe}'}}) RETURN n.link"
            results = self.show(query)
            return [r[0] if isinstance(r, (list, tuple)) else r.get('n.link', '') for r in results]
        except Exception as e:
            print(f"Get session nodes error: {e}")
            return []

    def test(self):
        """Test connection"""
        try:
            result = self.conn.execute("CALL SHOW_TABLES() RETURN *")
            print(list(result))
        except Exception as e:
            print(f"Test failed: {e}")

    def _escape(self, text: str) -> str:
        """Escape single quotes in strings"""
        if not isinstance(text, str):
            text = str(text)
        return text.replace("'", "\\'")

    def __del__(self):
        """Close connection"""
        try:
            self.conn.close()
        except:
            pass
```
---
**File:** `/home/randomguy/surjo/projs/arabella/db/QdrantDB.py`
```python
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import numpy as np
from typing import List, Optional, Dict, Any

class QdrantDB:
    def __init__(
        self,
        path: str = "./vector_db",
        collection_name: str = "nodes",
        vector_size: int = 768
    ):
        self.client = QdrantClient(path=path)
        self.collection = collection_name
        self.vector_size = vector_size
        
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                ),
            )

    def upsert_points(
        self,
        ids: List[str],
        vectors: List[List[float]],
        payloads: Optional[List[Dict[str, Any]]] = None
    ):
        """Upsert points into collection"""
        if payloads is None:
            payloads = [{}] * len(ids)
        
        points = []
        for i, (id_val, v, p) in enumerate(zip(ids, vectors, payloads)):
            point_id = abs(hash(id_val)) % (2**31)
            point = PointStruct(
                id=point_id,
                vector=np.array(v).astype(np.float32).tolist(),
                payload=p
            )
            points.append(point)
        
        self.client.upsert(collection_name=self.collection, points=points)

    def query(
        self,
        vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.0
    ) -> List[Any]:
        """Query collection and return results"""
        results = self.client.search(
            collection_name=self.collection,
            query_vector=np.array(vector).astype(np.float32).tolist(),
            limit=limit,
            score_threshold=score_threshold
        )
        return results

    def delete_collection(self):
        """Delete entire collection"""
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(collection_name=self.collection)

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection metadata"""
        try:
            return self.client.get_collection(self.collection)
        except:
            return {"status": "collection not found"}

    def clear_collection(self):
        """Clear all points from collection"""
        self.delete_collection()
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE
            ),
        )
```
---
**File:** `/home/randomguy/surjo/projs/arabella/graph_schema.sql`
```sql
CREATE NODE TABLE links(linkid SERIAL PRIMARY KEY, link STRING, session_id STRING);
CREATE REL TABLE hyprlink(FROM links TO links, session_id STRING);
```
---
**File:** `/home/randomguy/surjo/projs/arabella/main.py`
```python
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
```
---
**File:** `/home/randomguy/surjo/projs/arabella/query_bridge/__init__.py`
```python
```
---
**File:** `/home/randomguy/surjo/projs/arabella/rag/__init__.py`
```python
import ollama
from db.QdrantDB import QdrantDB
from db.KuzuDB import KuzuDB
from typing import List, Dict, Any, Optional
import re

try:
    import semchunk
    HAS_SEMCHUNK = True
except ImportError:
    HAS_SEMCHUNK = False
    print("Warning: semchunk not available, using fallback chunking")


class GraphRAG:
    def __init__(
        self,
        embedding_model: str = 'nomic-embed-text:v1.5',
        language_model: str = 'llama3.2:3b',
        vector_size: int = 768,
        kuzu_db_path: str = "./kuzu_db",
        qdrant_path: str = "./vector_db"
    ):
        self.embedding_model = embedding_model
        self.language_model = language_model
        self.vector_db = QdrantDB(path=qdrant_path, vector_size=vector_size)
        self.graph_db = KuzuDB(kuzu_db_path)
        self.chunk_size = 256
        self.max_graph_depth = 2

    def chunk_text(self, text: str) -> List[str]:
        """Chunk text using semantic chunking or fallback"""
        if not text or len(text.strip()) == 0:
            return []
        
        try:
            if HAS_SEMCHUNK:
                chunker = semchunk.chunkerify('gpt-4', self.chunk_size)
                return chunker(text)
        except Exception as e:
            print(f"Semchunk error: {e}, using fallback")
        
        # Fallback: simple word-based chunking
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size > self.chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def embed_text(self, text: str) -> List[float]:
        """Generate embeddings using Ollama"""
        try:
            resp = ollama.embed(model=self.embedding_model, input=text)
            return resp["embeddings"][0]
        except Exception as e:
            print(f"Embedding error: {e}")
            return [0.0] * 768  # Return zero vector on error

    def index_document(
        self,
        doc_id: str,
        url: str,
        content: str,
        session_id: str
    ) -> bool:
        """Index a document into both vector and graph databases"""
        try:
            # Insert node into graph DB
            self.graph_db.insert_node(url, session_id)
            
            # Chunk and embed content
            chunks = self.chunk_text(content)
            if not chunks:
                print(f"Warning: No chunks generated for {url}")
                return False
            
            vectors = [self.embed_text(chunk) for chunk in chunks]
            
            # Prepare payloads with document metadata
            ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
            payloads = [
                {
                    "doc_id": doc_id,
                    "url": url,
                    "chunk_idx": i,
                    "text": chunk,
                    "session_id": session_id
                }
                for i, chunk in enumerate(chunks)
            ]
            
            # Store in vector DB
            self.vector_db.upsert_points(ids, vectors, payloads)
            return True
        
        except Exception as e:
            print(f"Index document error: {e}")
            return False

    def link_documents(self, from_url: str, to_url: str, session_id: str) -> bool:
        """Create edge between two documents in graph DB"""
        try:
            self.graph_db.insert_rel(from_url, to_url, session_id)
            return True
        except Exception as e:
            print(f"Error linking documents: {e}")
            return False

    def retrieve_with_graph_traversal(
        self,
        query: str,
        session_id: str,
        top_k: int = 5,
        use_graph: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using:
        1. Vector similarity search (semantic)
        2. Graph traversal to find related documents
        """
        try:
            # Step 1: Vector search for semantically relevant chunks
            query_vec = self.embed_text(query)
            vector_results = self.vector_db.query(query_vec, limit=top_k)
            
            retrieved_docs = []
            retrieved_urls = set()
            
            # Convert vector results to document format
            for result in vector_results:
                payload = result.payload
                url = payload.get("url")
                retrieved_urls.add(url)
                retrieved_docs.append({
                    "type": "vector_search",
                    "url": url,
                    "text": payload.get("text"),
                    "score": float(result.score),
                    "doc_id": payload.get("doc_id"),
                    "depth": 0
                })
            
            # Step 2: Graph traversal to find related documents
            if use_graph and retrieved_docs:
                for doc in retrieved_docs[:]:
                    url = doc["url"]
                    related_docs = self._traverse_graph(url, session_id, depth=0)
                    
                    for related in related_docs:
                        if related["url"] not in retrieved_urls:
                            retrieved_docs.append(related)
                            retrieved_urls.add(related["url"])
            
            return retrieved_docs
        
        except Exception as e:
            print(f"Retrieval error: {e}")
            return []

    def _traverse_graph(
        self,
        start_url: str,
        session_id: str,
        depth: int = 0,
        max_depth: int = 2,
        visited: Optional[set] = None
    ) -> List[Dict[str, Any]]:
        """Recursively traverse graph to find related documents"""
        if visited is None:
            visited = set()
        
        if depth >= max_depth or start_url in visited:
            return []
        
        visited.add(start_url)
        related_docs = []
        
        try:
            neighbors = self.graph_db.get_neighbors(start_url, session_id, depth=1)
            
            for url in neighbors:
                if url and url not in visited:
                    related_docs.append({
                        "type": "graph_traversal",
                        "url": url,
                        "text": f"Related document from knowledge graph",
                        "score": 0.5 ** (depth + 1),
                        "depth": depth + 1
                    })
                    
                    # Continue traversal
                    deeper = self._traverse_graph(
                        url, session_id, depth + 1, max_depth, visited
                    )
                    related_docs.extend(deeper)
        
        except Exception as e:
            print(f"Graph traversal error: {e}")
        
        return related_docs

    def aggregate_context(self, docs: List[Dict[str, Any]]) -> str:
        """Aggregate retrieved documents into a cohesive context"""
        context_parts = []
        
        # Sort by depth (prefer closer nodes) and score
        sorted_docs = sorted(
            docs,
            key=lambda x: (x.get("depth", 0), -x.get("score", 0))
        )
        
        for doc in sorted_docs[:10]:
            text = doc.get("text", "")
            url = doc.get("url", "")
            doc_type = doc.get("type", "")
            
            if text and text.strip():
                context_parts.append(f"[{doc_type}] {url}:\n{text}")
        
        return "\n\n".join(context_parts) if context_parts else "No context found."

    def generate_response(self, query: str, context: str) -> str:
        """Generate response using LLM with aggregated context"""
        try:
            system_prompt = """You are an intelligent assistant with access to a knowledge graph.
Use the provided context from related documents to answer the user's query comprehensively.
When citing information, reference the source documents when possible.
If context is insufficient, acknowledge limitations and provide what you know."""
            
            response = ollama.chat(
                model=self.language_model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Context from knowledge graph:\n{context}\n\nUser question: {query}"}
                ]
            )
            
            return response["message"]["content"]
        
        except Exception as e:
            print(f"Generation error: {e}")
            return f"Error generating response: {str(e)}"

    def answer(self, query: str, session_id: str) -> str:
        """Complete Graph-RAG pipeline: retrieve -> aggregate -> generate"""
        try:
            # Retrieve with graph traversal
            docs = self.retrieve_with_graph_traversal(query, session_id, top_k=5, use_graph=True)
            
            if not docs:
                return "No relevant documents found in knowledge graph."
            
            # Aggregate context from graph and vectors
            context = self.aggregate_context(docs)
            
            # Generate response
            response = self.generate_response(query, context)
            
            return response
        
        except Exception as e:
            print(f"Answer error: {e}")
            return f"Error: {str(e)}"

    def bulk_index_from_crawler(
        self,
        crawler_relations: List[tuple],
        documents: Dict[str, str],
        session_id: str
    ) -> bool:
        """
        Index documents from web crawler output
        
        Args:
            crawler_relations: List of (parent_url, child_url) tuples
            documents: Dict mapping URL -> content
            session_id: Session identifier for grouping
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Index all documents
            for i, (url, content) in enumerate(documents.items()):
                doc_id = url.replace("https://", "").replace("http://", "").replace("/", "_")[:50]
                success = self.index_document(doc_id, url, content, session_id)
                if not success:
                    print(f"Warning: Failed to index {url}")
            
            # Create graph links
            for parent_url, child_url in crawler_relations:
                self.link_documents(parent_url, child_url, session_id)
            
            print(f"Indexed {len(documents)} documents with {len(crawler_relations)} relationships")
            return True
        
        except Exception as e:
            print(f"Bulk index error: {e}")
            return False
```
---
**File:** `/home/randomguy/surjo/projs/arabella/README.md`
```markdown
# Arabella
## Installation
To download the repo run
### Windows
```bash
git clone https://github.com/iamsurjog/Arabella.git
py -m venv ./.venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Linux
```bash
git clone https://github.com/iamsurjog/Arabella.git
py -m venv ./.venv
source .venv/bin/activate
pip install -r requirements.txt
```
## Running it
### Windows
```bash
.\.venv\Scripts\activate
fastapi run main.py
```

### Linux
```bash
source .venv/bin/activate
fastapi run main.py
```
```
---
**File:** `/home/randomguy/surjo/projs/arabella/requirements.txt`
```
annotated-doc==0.0.3
annotated-types==0.7.0
anyio==4.11.0
beautifulsoup4==4.14.2
certifi==2025.10.5
charset-normalizer==3.4.4
click==8.3.0
dnspython==2.8.0
email-validator==2.3.0
fastapi==0.120.4
fastapi-cli==0.0.14
fastapi-cloud-cli==0.3.1
h11==0.16.0
httpcore==1.0.9
httptools==0.7.1
httpx==0.28.1
idna==3.11
Jinja2==3.1.6
markdown-it-py==4.0.0
MarkupSafe==3.0.3
mdurl==0.1.2
ollama==0.6.0
pydantic==2.12.3
pydantic_core==2.41.4
Pygments==2.19.2
python-dotenv==1.2.1
python-multipart==0.0.20
PyYAML==6.0.3
requests==2.32.5
rich==14.2.0
rich-toolkit==0.15.1
rignore==0.7.3
sentry-sdk==2.43.0
shellingham==1.5.4
sniffio==1.3.1
soupsieve==2.8
starlette==0.49.2
typer==0.20.0
typing-inspection==0.4.2
typing_extensions==4.15.0
urllib3==2.5.0
uvicorn==0.38.0
uvloop==0.22.1
watchfiles==1.1.1
websockets==15.0.1
```
---
**File:** `/home/randomguy/surjo/projs/arabella/scripts/config.py`
```python
import yaml

def config():
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    return config
```
---
**File:** `/home/randomguy/surjo/projs/arabella/scripts/init_databases.py`
```python
from db.QdrantDB import QdrantDB
from db.KuzuDB import KuzuDB
from rag import GraphRAG

def initialize_system():
    """Initialize all database systems"""
    print("=" * 50)
    print("Initializing Arabella System")
    print("=" * 50)
    
    try:
        # Initialize vector DB
        print("\n[1/3] Initializing Qdrant Vector DB...")
        vector_db = QdrantDB(
            path="./vector_db",
            collection_name="nodes",
            vector_size=768
        )
        info = vector_db.get_collection_info()
        print(f"✓ Qdrant initialized: {info}")
        
        # Initialize graph DB
        print("\n[2/3] Initializing KuzuDB Graph DB...")
        graph_db = KuzuDB("./kuzu_db")
        graph_db.test()
        print("✓ KuzuDB initialized")
        
        # Initialize Graph-RAG
        print("\n[3/3] Initializing Graph-RAG Pipeline...")
        rag = GraphRAG(
            embedding_model='nomic-embed-text:v1.5',
            language_model='llama3.2:3b',
            vector_size=768,
            kuzu_db_path="./kuzu_db",
            qdrant_path="./vector_db"
        )
        print("✓ Graph-RAG pipeline initialized")
        
        print("\n" + "=" * 50)
        print("System ready for operation!")
        print("=" * 50)
        return True
    
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        return False

if __name__ == "__main__":
    initialize_system()
```
