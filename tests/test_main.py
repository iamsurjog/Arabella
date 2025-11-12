import pytest
from fastapi.testclient import TestClient
from main import app


class TestMainAPI:
    """Integration tests for main API"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        return TestClient(app)
    
    def test_query_endpoint_structure(self, client):
        """Test that query endpoint accepts correct structure"""
        response = client.post("/query", json={
            "query": "test query",
            "new_session": True
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
    
    def test_graph_endpoint(self, client):
        """Test graph endpoint"""
        response = client.post("/graph", json={
            "session_id": "test-session"
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
    
    def test_answer_endpoint(self, client):
        """Test answer endpoint"""
        response = client.get("/answer")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def client(self):
        """Create a test client"""
        return TestClient(app)
    
    def test_full_query_pipeline(self, client, sample_documents):
        """Test the full query pipeline (mock required)"""
        # This would require mocking the crawler and LLM
        # For now, just test the endpoint structure
        response = client.post("/query", json={
            "query": "What is Python?",
            "new_session": True
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "query" in data
