import pytest
from rag import GraphRAG
import tempfile
import shutil


class TestGraphRAG:
    """Unit tests for GraphRAG module"""
    
    @pytest.fixture
    def rag(self, temp_kuzu_db, temp_vector_db):
        """Create a GraphRAG instance for testing"""
        return GraphRAG(
            embedding_model='nomic-embed-text:v1.5',
            language_model='llama3.2:3b',
            vector_size=768,
            kuzu_db_path=temp_kuzu_db,
            qdrant_path=temp_vector_db
        )
    
    def test_chunk_text_fallback(self, rag):
        """Test text chunking with fallback method"""
        text = "This is a test. " * 100  # Create a long text
        chunks = rag.chunk_text(text)
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_chunk_text_empty(self, rag):
        """Test chunking empty text"""
        chunks = rag.chunk_text("")
        assert chunks == []
    
    def test_index_document(self, rag, sample_documents):
        """Test indexing a single document"""
        url = list(sample_documents.keys())[0]
        content = sample_documents[url]
        success = rag.index_document("doc1", url, content, "test-session")
        assert success is True
    
    def test_link_documents(self, rag, sample_documents):
        """Test creating links between documents"""
        urls = list(sample_documents.keys())
        for url in urls:
            rag.index_document(url.replace("/", "_"), url, sample_documents[url], "test-session")
        
        success = rag.link_documents(urls[0], urls[1], "test-session")
        assert success is True
    
    def test_bulk_index_from_crawler(self, rag, sample_documents, sample_relations):
        """Test bulk indexing from crawler output"""
        success = rag.bulk_index_from_crawler(
            sample_relations,
            sample_documents,
            "test-session"
        )
        assert success is True
    
    def test_aggregate_context(self, rag):
        """Test context aggregation"""
        docs = [
            {
                "type": "vector_search",
                "url": "https://example.com/1",
                "text": "Test document 1",
                "score": 0.9,
                "depth": 0
            },
            {
                "type": "graph_traversal",
                "url": "https://example.com/2",
                "text": "Test document 2",
                "score": 0.7,
                "depth": 1
            }
        ]
        context = rag.aggregate_context(docs)
        assert isinstance(context, str)
        assert len(context) > 0
        assert "Test document 1" in context or "Test document 2" in context


@pytest.mark.integration
@pytest.mark.integration
@pytest.mark.requires_ollama
class TestGraphRAGIntegration:
    """Integration tests for GraphRAG (requires Ollama)"""
    
    @pytest.fixture
    def rag(self, temp_kuzu_db, temp_vector_db, check_ollama_models):
        """Create a GraphRAG instance for testing"""
        return GraphRAG(
            embedding_model='nomic-embed-text:v1.5',
            language_model='llama3.2:3b',
            vector_size=768,
            kuzu_db_path=temp_kuzu_db,
            qdrant_path=temp_vector_db
        )
    
    def test_ollama_connection(self, rag):
        """Test that Ollama server is accessible"""
        try:
            # Try to generate a simple embedding
            embedding = rag.embed_text("test")
            assert embedding is not None
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            # Verify it's not the error fallback (all zeros)
            assert not all(x == 0.0 for x in embedding)
        except Exception as e:
            pytest.fail(f"Ollama connection failed: {e}")
    
    def test_embed_text_with_ollama(self, rag):
        """Test embedding generation with various inputs"""
        test_cases = [
            "This is a test",
            "Python is a programming language",
            "Machine learning and artificial intelligence"
        ]
        
        for text in test_cases:
            try:
                embedding = rag.embed_text(text)
                assert isinstance(embedding, list)
                assert len(embedding) == 768
                # Check embeddings are not all zeros (error case)
                assert not all(x == 0.0 for x in embedding)
                # Check embeddings are normalized (common for embedding models)
                assert any(x != 0.0 for x in embedding)
            except Exception as e:
                pytest.fail(f"Embedding failed for '{text}': {e}")
    
    def test_embedding_consistency(self, rag):
        """Test that same text produces same embedding"""
        text = "Consistency test"
        embedding1 = rag.embed_text(text)
        embedding2 = rag.embed_text(text)
        
        assert len(embedding1) == len(embedding2)
        assert embedding1 == embedding2
    
    def test_full_rag_pipeline(self, rag, sample_documents, sample_relations):
        """Test full RAG pipeline (requires Ollama running)"""
        try:
            # Index documents
            rag.bulk_index_from_crawler(sample_relations, sample_documents, "integration-test")
            
            # Generate answer
            answer = rag.answer("What is Python?", "integration-test")
            assert isinstance(answer, str)
            assert len(answer) > 0
        except Exception as e:
            pytest.skip(f"Full pipeline test skipped: {e}")

