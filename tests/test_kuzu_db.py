import pytest
from db.KuzuDB import KuzuDB
import tempfile
import shutil


class TestKuzuDB:
    """Unit tests for KuzuDB module"""
    
    @pytest.fixture
    def db(self, temp_kuzu_db):
        """Create a KuzuDB instance for testing"""
        return KuzuDB(temp_kuzu_db)
    
    def test_init_schema(self, db):
        """Test database schema initialization"""
        # Should not raise an exception
        assert db.conn is not None
        assert db.db is not None
    
    def test_insert_node(self, db):
        """Test inserting a node"""
        db.insert_node("https://example.com", "test-session-1")
        nodes = db.get_session_nodes("test-session-1")
        assert len(nodes) >= 1
        assert "https://example.com" in nodes
    
    def test_insert_relationship(self, db):
        """Test inserting a relationship between nodes"""
        # First insert nodes
        db.insert_node("https://example.com/page1", "test-session-2")
        db.insert_node("https://example.com/page2", "test-session-2")
        
        # Then create relationship
        db.insert_rel("https://example.com/page1", "https://example.com/page2", "test-session-2")
        
        # Verify relationship exists
        neighbors = db.get_neighbors("https://example.com/page1", "test-session-2", depth=1)
        assert "https://example.com/page2" in neighbors
    
    def test_get_session_nodes(self, db):
        """Test getting all nodes in a session"""
        session_id = "test-session-3"
        db.insert_node("https://example.com/a", session_id)
        db.insert_node("https://example.com/b", session_id)
        db.insert_node("https://example.com/c", session_id)
        
        nodes = db.get_session_nodes(session_id)
        assert len(nodes) == 3
        assert "https://example.com/a" in nodes
        assert "https://example.com/b" in nodes
        assert "https://example.com/c" in nodes
    
    def test_escape_method(self, db):
        """Test SQL escaping"""
        escaped = db._escape("test'quote")
        assert "\\'" in escaped or escaped.count("'") == 0
    
    def test_session_isolation(self, db):
        """Test that different sessions are isolated"""
        db.insert_node("https://example.com/x", "session-a")
        db.insert_node("https://example.com/y", "session-b")
        
        nodes_a = db.get_session_nodes("session-a")
        nodes_b = db.get_session_nodes("session-b")
        
        assert "https://example.com/x" in nodes_a
        assert "https://example.com/x" not in nodes_b
        assert "https://example.com/y" not in nodes_a
        assert "https://example.com/y" in nodes_b
