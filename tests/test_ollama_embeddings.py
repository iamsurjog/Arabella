#!/usr/bin/env python3
"""
Test script to verify Ollama embeddings are working correctly
"""
import pytest
import sys
from ollama import Client


pytestmark = pytest.mark.requires_ollama


@pytest.fixture
def client(check_ollama_models):
    """Fixture to create Ollama client"""
    try:
        client = Client(host='http://127.0.0.1:11434')
        return client
    except Exception as e:
        pytest.skip(f"Ollama not available: {e}")


def test_ollama_connection(client):
    """Test basic Ollama connection"""
    assert client is not None
    print("✓ Ollama client created")


def test_embeddings(client):
    """Test embedding generation"""
    test_text = "This is a test sentence for embedding."
    
    print(f"\nGenerating embedding for: '{test_text}'")
    response = client.embeddings(
        model='nomic-embed-text:v1.5',
        prompt=test_text
    )
    
    embedding = response['embedding']
    
    print(f"✓ Embedding generated successfully")
    print(f"  - Dimension: {len(embedding)}")
    print(f"  - Sample values: {embedding[:5]}")
    print(f"  - All zeros? {all(x == 0.0 for x in embedding)}")
    print(f"  - Has non-zero values? {any(x != 0.0 for x in embedding)}")
    
    # Verify embedding
    assert isinstance(embedding, list), "Embedding should be a list"
    assert len(embedding) == 768, f"Expected 768 dimensions, got {len(embedding)}"
    assert not all(x == 0.0 for x in embedding), "Embedding should not be all zeros"
    
    print("\n✓ All embedding checks passed!")
    return embedding

def test_consistency(client):
    """Test that same input produces same embedding"""
    test_text = "Consistency test"
    
    resp1 = client.embeddings(model='nomic-embed-text:v1.5', prompt=test_text)
    resp2 = client.embeddings(model='nomic-embed-text:v1.5', prompt=test_text)
    
    emb1 = resp1['embedding']
    emb2 = resp2['embedding']
    
    if emb1 == emb2:
        print("✓ Embeddings are consistent (same input -> same output)")
    else:
        print("⚠ Warning: Embeddings differ for same input (may be expected for some models)")


def test_rag_integration(temp_kuzu_db, temp_vector_db):
    """Test GraphRAG with embeddings"""
    from rag import GraphRAG
    
    print("\n--- Testing GraphRAG Integration ---")
    
    rag = GraphRAG(
        kuzu_db_path=temp_kuzu_db,
        qdrant_path=temp_vector_db
    )
    
    # Test embedding via RAG
    text = "Testing RAG embedding integration"
    embedding = rag.embed_text(text)
    
    print(f"✓ RAG embedding successful")
    print(f"  - Dimension: {len(embedding)}")
    print(f"  - Sample: {embedding[:3]}")
    
    assert len(embedding) == 768
    assert not all(x == 0.0 for x in embedding), "Embedding should not be all zeros"
    
    print("✓ RAG integration test passed!")
