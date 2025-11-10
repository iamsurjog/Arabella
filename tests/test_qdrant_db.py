import pytest
from db.QdrantDB import QdrantDB
import numpy as np


class TestQdrantDB:
    """Unit tests for QdrantDB module"""
    
    @pytest.fixture
    def db(self, temp_vector_db):
        """Create a QdrantDB instance for testing"""
        return QdrantDB(path=temp_vector_db, collection_name="test_collection", vector_size=768)
    
    def test_init_collection(self, db):
        """Test collection initialization"""
        info = db.get_collection_info()
        assert info is not None
    
    def test_upsert_points(self, db):
        """Test upserting points into collection"""
        ids = ["test1", "test2", "test3"]
        vectors = [
            np.random.rand(768).tolist(),
            np.random.rand(768).tolist(),
            np.random.rand(768).tolist()
        ]
        payloads = [
            {"text": "First document", "url": "https://example.com/1"},
            {"text": "Second document", "url": "https://example.com/2"},
            {"text": "Third document", "url": "https://example.com/3"}
        ]
        
        db.upsert_points(ids, vectors, payloads)
        
        # Query to verify
        results = db.query(vectors[0], limit=3)
        assert len(results) > 0
    
    def test_query(self, db):
        """Test querying the collection"""
        # First insert some data
        ids = ["query_test1"]
        vectors = [np.random.rand(768).tolist()]
        payloads = [{"text": "Query test document"}]
        
        db.upsert_points(ids, vectors, payloads)
        
        # Query with the same vector
        results = db.query(vectors[0], limit=1)
        assert len(results) > 0
        assert results[0].payload["text"] == "Query test document"
    
    def test_clear_collection(self, db):
        """Test clearing collection"""
        # Insert data
        ids = ["clear1"]
        vectors = [np.random.rand(768).tolist()]
        db.upsert_points(ids, vectors)
        
        # Clear collection
        db.clear_collection()
        
        # Verify it's empty
        results = db.query(vectors[0], limit=10)
        assert len(results) == 0
    
    def test_delete_collection(self, db):
        """Test deleting collection"""
        db.delete_collection()
        info = db.get_collection_info()
        assert info.get("status") == "collection not found" or "error" in str(info).lower()
