import pytest
from query_bridge import QueryBridge


class TestQueryBridge:
    """Unit tests for QueryBridge module"""
    
    @pytest.fixture
    def bridge(self):
        """Create a QueryBridge instance"""
        return QueryBridge()
    
    def test_transform_simple_query(self, bridge):
        """Test transformation of simple query"""
        query = "What is Python?"
        result = bridge.transform(query)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "python" in result.lower()
    
    def test_transform_complex_query(self, bridge):
        """Test transformation of complex query"""
        query = "How does machine learning work and what are its applications?"
        result = bridge.transform(query)
        assert isinstance(result, str)
        assert "machine" in result.lower() or "learning" in result.lower()
    
    def test_transform_removes_stopwords(self, bridge):
        """Test that stopwords are removed"""
        query = "What is the best way to learn Python programming?"
        result = bridge.transform(query)
        # Stopwords like 'what', 'is', 'the' should be removed
        assert "what" not in result.lower()
        assert "the" not in result.lower()
    
    def test_transform_empty_query(self, bridge):
        """Test handling of empty query"""
        query = ""
        result = bridge.transform(query)
        # Should return original or empty string
        assert isinstance(result, str)
    
    def test_transform_single_word(self, bridge):
        """Test transformation of single word query"""
        query = "Python"
        result = bridge.transform(query)
        assert isinstance(result, str)
        assert "python" in result.lower()
