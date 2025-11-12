import pytest
import tempfile
import shutil
from pathlib import Path


def check_ollama_model_available(model_name: str) -> bool:
    """Check if an Ollama model is available"""
    try:
        from ollama import Client
        client = Client(host='http://127.0.0.1:11434')
        models = client.list()
        model_names = [m.get('name', '') for m in models.get('models', [])]
        return any(model_name in name for name in model_names)
    except Exception:
        return False


@pytest.fixture
def ollama_client():
    """Fixture to provide Ollama client, skip if not available"""
    try:
        from ollama import Client
        client = Client(host='http://127.0.0.1:11434')
        # Test connection
        client.list()
        return client
    except Exception as e:
        pytest.skip(f"Ollama not available: {e}")


@pytest.fixture(scope="session")
def check_ollama_models():
    """Session-scoped fixture to check if required models are available"""
    required_models = ["nomic-embed-text:v1.5", "llama3.2:3b"]
    missing_models = [m for m in required_models if not check_ollama_model_available(m)]
    
    if missing_models:
        pytest.skip(
            f"Required Ollama models not found: {', '.join(missing_models)}\n"
            f"Run: make setup-ollama"
        )


@pytest.fixture
def temp_kuzu_db():
    """Create a temporary KuzuDB directory for testing"""
    # Create a parent temp directory
    parent_dir = tempfile.mkdtemp()
    # KuzuDB will create the actual database directory itself
    db_path = Path(parent_dir) / "test_kuzu_db"
    yield str(db_path)
    # Clean up the parent directory (which includes the db)
    shutil.rmtree(parent_dir, ignore_errors=True)


@pytest.fixture
def temp_vector_db():
    """Create a temporary vector database directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return {
        "https://example.com/page1": "This is a test document about Python programming.",
        "https://example.com/page2": "Machine learning is a subset of artificial intelligence.",
        "https://example.com/page3": "Graph databases are useful for connected data."
    }


@pytest.fixture
def sample_relations():
    """Sample relations for testing"""
    return [
        ("https://example.com/page1", "https://example.com/page2"),
        ("https://example.com/page1", "https://example.com/page3"),
    ]
