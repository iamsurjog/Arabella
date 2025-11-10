from ollama import Client
from db.QdrantDB import QdrantDB
from db.KuzuDB import KuzuDB
from typing import List, Dict, Any, Optional
import os

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
        qdrant_path: str = "./vector_db",
        ollama_host: str = None
    ):
        self.embedding_model = embedding_model
        self.language_model = language_model
        self.vector_db = QdrantDB(path=qdrant_path, vector_size=vector_size)
        self.graph_db = KuzuDB(kuzu_db_path)
        self.chunk_size = 256
        self.max_graph_depth = 2
        
        # Initialize Ollama client with proper host
        if ollama_host is None:
            ollama_host = os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434')
        self.ollama_client = Client(host=ollama_host)

    def chunk_text(self, text: str) -> List[str]:
        """Chunk text using semantic chunking or fallback"""
        if not text or len(text.strip()) == 0:
            return []
        
        try:
            if HAS_SEMCHUNK:
                # Use a token-based chunker instead of model-based
                # semchunk supports 'o200k_base' which is tiktoken's encoding
                chunker = semchunk.chunkerify('o200k_base', self.chunk_size)
                return chunker(text)
        except Exception as e:
            # Silently fall back to simple chunking
            pass
        
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
            resp = self.ollama_client.embeddings(model=self.embedding_model, prompt=text)
            # Ensure we have a valid embedding
            embedding = resp.get("embedding")
            if not embedding:
                raise ValueError("No embedding returned from Ollama")
            if not isinstance(embedding, list):
                raise ValueError(f"Invalid embedding type: {type(embedding)}")
            return embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            # Return zero vector on error with correct dimension based on model
            return [0.0] * 768  # nomic-embed-text:v1.5 uses 768 dimensions

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
            
            response = self.ollama_client.chat(
                model=self.language_model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Context from knowledge graph:\n{context}\n\nUser question: {query}"}
                ]
            )
            
            # Ensure we have a valid response
            if not response:
                raise ValueError("No response from Ollama")
            
            message = response.get("message")
            if not message:
                raise ValueError("No message in Ollama response")
            
            content = message.get("content")
            if not content:
                raise ValueError("No content in message")
            
            return content
        
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
            # Index all documents with progress
            total = len(documents)
            print(f"Indexing {total} documents...")
            for i, (url, content) in enumerate(documents.items(), 1):
                doc_id = url.replace("https://", "").replace("http://", "").replace("/", "_")[:50]
                success = self.index_document(doc_id, url, content, session_id)
                if not success:
                    print(f"Warning: Failed to index {url}")
                else:
                    print(f"  [{i}/{total}] Indexed: {url}")
            
            # Create graph links
            print(f"Creating {len(crawler_relations)} relationships...")
            for parent_url, child_url in crawler_relations:
                self.link_documents(parent_url, child_url, session_id)
            
            print(f"✓ Indexed {len(documents)} documents with {len(crawler_relations)} relationships")
            return True
        
        except Exception as e:
            print(f"Bulk index error: {e}")
            return False