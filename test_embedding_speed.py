#!/usr/bin/env python3
"""
Quick test of embedding generation speed
"""
import sys
import time
sys.path.insert(0, '/home/hydenix/repos/Arabella')

from rag import GraphRAG

print("Testing embedding generation speed...")
print("-" * 60)

rag = GraphRAG(
    embedding_model='nomic-embed-text:v1.5',
    language_model='llama3.2:3b',
    vector_size=768,
    kuzu_db_path="./test_kuzu_db",
    qdrant_path="./test_vector_db"
)

test_texts = [
    "Short text",
    "Medium length text that is a bit longer but not too long",
    "This is a longer text that contains multiple sentences. It should help us understand how the embedding generation performs with more content. We want to measure the time it takes.",
]

for i, text in enumerate(test_texts, 1):
    print(f"\nTest {i}: {len(text)} characters")
    start = time.time()
    
    try:
        embedding = rag.embed_text(text)
        elapsed = time.time() - start
        
        print(f"  ✓ Generated embedding in {elapsed:.2f}s")
        print(f"  ✓ Dimension: {len(embedding)}")
        print(f"  ✓ Sample values: {embedding[:5]}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "-" * 60)
print("Test completed!")
