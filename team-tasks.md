# Team Task Assignments & Integration Guide

---

## Overview

Your project **Arabella** is structured as:
```
arabella/
├── config.yaml              (LLM/embedding config)
├── requirements.txt         (dependencies)
├── main.py                  (FastAPI endpoints)
├── crawler/                 (web crawling)
├── query_bridge/            (query transformation - PERSON 2)
├── rag/                     (retrieval & generation - YOUR RESPONSIBILITY)
├── db/                      (database layer - YOUR RESPONSIBILITY)
├── scripts/                 (utilities & initialization)
└── graph_schema.sql         (KuzuDB schema)
```

**Backend Flow**:
```
User Query (Frontend)
    ↓
main.py (FastAPI)
    ↓
query_bridge/ (Person 2) → transforms natural language to search query
    ↓
crawler/ (Person 1) → crawls web using search query
    ↓
db/ (YOU) → stores in KuzuDB + Qdrant
    ↓
rag/ (YOU) → Graph-RAG retrieval & generation
    ↓
main.py returns response to Frontend
```

---

## PERSON 1: Backend Integration

**Responsibility**: Connect crawler output to your RAG pipeline

### What They Need to Provide:

From `crawler/__init__.py`, the `crawl_relations()` function returns:
```python
(link_text_map, relations) = crawl_relations(url, max_depth=2)
# link_text_map: Dict[str, str] -> {url: plain_text_content}
# relations: List[tuple] -> [(parent_url, child_url), ...]
```

### Integration Point in `main.py`:

Person 1 should update the `/query` endpoint:

```python
from crawler import crawl_relations
from rag import GraphRAG
import uuid

rag = GraphRAG()

@app.post("/query")
async def query(query_data: QueryBaseModel):
    session_id = str(uuid.uuid4()) if query_data.new_session else query_data.session_id
    
    # Step 1: Query Bridge transforms query (Person 2 handles this)
    search_query = query_bridge.transform(query_data.query)
    
    # Step 2: Crawler gets web results (Person 1 provides)
    link_text_map, relations = crawl_relations(search_query, max_depth=2)
    
    # Step 3: Index in Graph-RAG (YOUR responsibility)
    rag.bulk_index_from_crawler(relations, link_text_map, session_id)
    
    # Step 4: Generate answer
    answer = rag.answer(query_data.query, session_id)
    
    return {"session_id": session_id, "answer": answer, "query": query_data.query}
```

### Person 1's Checklist:
- [ ] Ensure `crawl_relations()` returns correct structure
- [ ] Handle errors gracefully (broken links, timeouts)
- [ ] Make sure plain text extraction is clean (no script/style tags)
- [ ] Return parent-child relationships correctly
- [ ] Test with a sample URL before integration

---

## PERSON 2: Query Bridge Module

**Responsibility**: Transform natural language queries into optimized Google search queries

### Module Location: `query_bridge/__init__.py`

### Input/Output Specification:

**Input**: Natural language question
```
"Explain how photosynthesis works and what is the role of chlorophyll"
```

**Output**: Concise search query (feature extraction)
```
"photosynthesis chlorophyll process"
```

### Requirements:

1. **Extract informational core** - Remove filler words, questions markers
2. **Keep key entities** - Preserve important nouns, concepts
3. **Stay concise** - 2-5 keywords optimal for search
4. **Remove stop words** - a, the, how, what, is, does
5. **Add domain context if needed** - e.g., "python" if asking about programming

### Implementation Template for Person 2:

```python
# query_bridge/__init__.py

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

class QueryBridge:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.stop_words.update(['how', 'what', 'why', 'when', 'where', 'which', 'who'])
    
    def transform(self, query: str) -> str:
        """
        Transform natural language query to search query
        
        Args:
            query: Natural language question
            
        Returns:
            Optimized search query string
            
        Example:
            "How does photosynthesis work?" → "photosynthesis process"
        """
        # TODO: Implement feature extraction
        # 1. Lowercase and tokenize
        # 2. Remove punctuation
        # 3. Filter stop words
        # 4. Extract entities (nouns, adjectives)
        # 5. Join and return
        pass
```

### Person 2's Checklist:
- [ ] Install NLTK: `pip install nltk`
- [ ] Download stopwords: `python -m nltk.downloader stopwords averaged_perceptron_tagger`
- [ ] Handle edge cases (single word, acronyms, etc.)
- [ ] Keep query length ≤ 7 words
- [ ] Test with diverse question types
- [ ] Return string output only

### Testing Their Code:

```python
from query_bridge import QueryBridge

bridge = QueryBridge()

test_cases = [
    ("What is artificial intelligence?", "artificial intelligence"),
    ("How do solar panels generate electricity?", "solar panels electricity"),
    ("Tell me about quantum computing", "quantum computing"),
]

for input_q, expected in test_cases:
    result = bridge.transform(input_q)
    print(f"Input: {input_q}")
    print(f"Output: {result}")
    print(f"Expected: {expected}\n")
```

---

## YOUR RESPONSIBILITY: RAG + DB Integration

### Code Location & Structure:

Implement:
- `db/QdrantDB.py` - Vector database operations
- `db/KuzuDB.py` - Update existing, add graph query methods
- `rag/__init__.py` - Graph-RAG pipeline
- `scripts/init_databases.py` - Initialization script

### Files to Update:
- `requirements.txt` - Add: `qdrant-client`, `semchunk`, `kuzu`, `numpy`
- `graph_schema.sql` - Ensure schema matches KuzuDB operations

### Integration Point with Team:

When Person 1 calls:
```python
rag.bulk_index_from_crawler(relations, link_text_map, session_id)
```

Your code should:
1. Create nodes in KuzuDB for each URL
2. Create edges for each (parent, child) relationship
3. Chunk text content
4. Generate embeddings for chunks
5. Store vectors in Qdrant
6. Link chunks to source documents

When they call:
```python
answer = rag.answer(query, session_id)
```

Your code should:
1. Generate embedding for query
2. Search Qdrant for similar chunks
3. Traverse KuzuDB graph to find related docs
4. Aggregate context from both sources
5. Use Ollama to generate final answer
6. Return response string

### Your Code Signature (for easy integration):

```python
# rag/__init__.py

class GraphRAG:
    def __init__(self, embedding_model='nomic-embed-text:v1.5', 
                 language_model='llama3.2:3b', 
                 vector_size=768,
                 kuzu_db_path="./kuzu_db",
                 qdrant_path="./vector_db"):
        pass
    
    def bulk_index_from_crawler(
        self, 
        crawler_relations: List[tuple],      # [(url1, url2), ...]
        documents: Dict[str, str],            # {url: content, ...}
        session_id: str                       # unique session identifier
    ) -> bool:
        """Index crawled documents with relationships"""
        pass
    
    def answer(
        self,
        query: str,                          # user query
        session_id: str                      # session to search in
    ) -> str:
        """Generate answer using Graph-RAG"""
        pass
```

---

## Updated requirements.txt

Add these to your existing `requirements.txt`:

```
# Existing packages (keep all)
annotated-doc==0.0.3
# ... (all existing packages)

# NEW - Database & Vector Storage
qdrant-client>=1.7.0
kuzu>=0.4.0
numpy>=1.24.0

# NEW - Text Processing
semchunk>=0.1.0
nltk>=3.8.1

# For better error handling (optional but recommended)
pydantic>=2.0.0
```

---

## Updated main.py Structure

Here's how the `/query` endpoint should look with all pieces:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from crawler import crawl_relations
from query_bridge import QueryBridge
from rag import GraphRAG
import uuid

app = FastAPI()
query_bridge = QueryBridge()
rag = GraphRAG()

class QueryBaseModel(BaseModel):
    session_id: str = ""
    query: str
    new_session: bool = True

@app.post("/query")
async def query(query_data: QueryBaseModel):
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
        session_id = str(uuid.uuid4()) if query_data.new_session else query_data.session_id
        
        # Step 2: Transform query (Person 2's module)
        search_query = query_bridge.transform(query_data.query)
        print(f"Transformed query: {search_query}")
        
        # Step 3: Crawl web (Person 1's module)
        link_text_map, relations = crawl_relations(search_query, max_depth=2)
        print(f"Crawled {len(link_text_map)} pages")
        
        # Step 4: Index in Graph-RAG (Your module)
        success = rag.bulk_index_from_crawler(relations, link_text_map, session_id)
        if not success:
            return {"error": "Failed to index documents"}
        
        # Step 5: Generate answer
        answer = rag.answer(query_data.query, session_id)
        
        # Step 6: Return
        return {
            "session_id": session_id,
            "query": query_data.query,
            "search_query": search_query,
            "answer": answer,
            "documents_indexed": len(link_text_map)
        }
    
    except Exception as e:
        return {"error": str(e)}
```

---

## Communication Protocol

### Person 1 (Backend/Crawler) provides:

**Function**: `crawl_relations(query: str, max_depth: int) -> Tuple[Dict, List]`

**Returns**:
- Dict: `{url: plain_text_content, ...}`
- List: `[(parent_url, child_url), ...]`

**Error handling**: Return empty dict/list on failure

---

### Person 2 (Query Bridge) provides:

**Function**: `transform(query: str) -> str`

**Returns**: 
- String of optimized search keywords

**Error handling**: Return original query on failure

---

### You (RAG/DB) provide:

**Function 1**: `bulk_index_from_crawler(relations, documents, session_id) -> bool`

**Function 2**: `answer(query: str, session_id: str) -> str`

**Error handling**: Return False or error message string

---

## Testing Workflow

### Before Integration:

1. **Person 1 tests crawler**:
   ```python
   from crawler import crawl_relations
   links, rels = crawl_relations("python programming", max_depth=2)
   assert len(links) > 0
   assert len(rels) > 0
   ```

2. **Person 2 tests query bridge**:
   ```python
   from query_bridge import QueryBridge
   bridge = QueryBridge()
   result = bridge.transform("What is machine learning?")
   assert isinstance(result, str)
   assert len(result) > 0
   ```

3. **You test Graph-RAG**:
   ```python
   from rag import GraphRAG
   rag = GraphRAG()
   
   # Mock data
   docs = {"https://example.com": "Sample content..."}
   rels = []
   session = "test-123"
   
   rag.bulk_index_from_crawler(rels, docs, session)
   answer = rag.answer("What is example?", session)
   assert isinstance(answer, str)
   ```

### Integration Testing:

Once each module is ready, test end-to-end:
```python
# Full pipeline test
response = requests.post("http://127.0.0.1:8000/query", json={
    "query": "What is climate change?",
    "new_session": True
})
print(response.json())
```

---

## Key Tips for Your Team

### For Person 1 (Backend):
- Use session IDs to group related queries
- Handle timeouts gracefully
- Cache crawl results if possible
- Ensure content extraction is Unicode-safe

### For Person 2 (Query Bridge):
- Test with typos and complex sentences
- Keep keywords domain-agnostic
- Avoid over-engineering (simple is better)
- Test with 50+ diverse queries

### For You (RAG/DB):
- Initialize databases once, reuse connections
- Implement batch operations for efficiency
- Use proper error handling and logging
- Test with different session IDs simultaneously
- Monitor vector DB size (prune old sessions if needed)

---

## File Checklist

**Your deliverables to Person 1**:
- ✅ `db/QdrantDB.py` - Full implementation
- ✅ `db/KuzuDB.py` - Updated with graph queries
- ✅ `rag/__init__.py` - GraphRAG class with required methods
- ✅ `scripts/init_databases.py` - Setup script
- ✅ Updated `requirements.txt`

**Person 1 deliverables to you**:
- ✅ Updated `crawler/__init__.py` with error handling
- ✅ Integration in `main.py` (your endpoint code)

**Person 2 deliverables to everyone**:
- ✅ `query_bridge/__init__.py` with `QueryBridge` class
- ✅ `transform(query: str) -> str` method

**Frontend team** (not your concern):
- UI calling `/query` endpoint with session management
