#!/usr/bin/env python3
"""
Simplified E2E test for Wikipedia crawling
"""
import sys
import tempfile
import shutil

sys.path.insert(0, '/home/hydenix/repos/Arabella')

from crawler import crawl_relations
from rag import GraphRAG
from query_bridge import QueryBridge

print("=" * 60)
print("E2E Wikipedia Test")
print("=" * 60)

# Create temporary directories
temp_dir = tempfile.mkdtemp(prefix="test_e2e_")
kuzu_dir = f"{temp_dir}/kuzu_db"
vector_dir = f"{temp_dir}/vector_db"

try:
    # Step 1: Initialize components
    print("\n1. Initializing components...")
    query_bridge = QueryBridge()
    rag = GraphRAG(
        embedding_model='nomic-embed-text:v1.5',
        language_model='llama3.2:3b',
        vector_size=768,
        kuzu_db_path=kuzu_dir,
        qdrant_path=vector_dir
    )
    print("   ✓ Components initialized")
    
    # Step 2: Crawl Wikipedia
    print("\n2. Crawling Wikipedia...")
    url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    link_text_map, relations = crawl_relations(url, max_depth=1, use_selenium=False)
    
    print(f"   ✓ Crawled {len(link_text_map)} pages")
    print(f"   ✓ Found {len(relations)} relationships")
    
    if not link_text_map:
        print("   ✗ No pages crawled!")
        sys.exit(1)
    
    # Step 3: Index documents (limit content for speed)
    print("\n3. Indexing documents...")
    session_id = "test-session"
    limited_content = {
        url: text[:2000] for url, text in link_text_map.items()
    }
    
    success = rag.bulk_index_from_crawler(relations, limited_content, session_id)
    if not success:
        print("   ✗ Indexing failed!")
        sys.exit(1)
    
    # Step 4: Test embedding
    print("\n4. Testing embeddings...")
    sample_text = list(limited_content.values())[0][:500]
    embedding = rag.embed_text(sample_text)
    
    if len(embedding) != 768:
        print(f"   ✗ Invalid embedding dimension: {len(embedding)}")
        sys.exit(1)
    
    print(f"   ✓ Generated embedding (dim={len(embedding)})")
    
    # Step 5: Test retrieval
    print("\n5. Testing retrieval...")
    query = "What is Python programming language?"
    docs = rag.retrieve_with_graph_traversal(query, session_id, top_k=3)
    
    print(f"   ✓ Retrieved {len(docs)} documents")
    for i, doc in enumerate(docs[:3], 1):
        print(f"      {i}. {doc.get('type')}: {doc.get('url', 'N/A')[:60]}...")
    
    # Step 6: Generate answer
    print("\n6. Generating answer...")
    answer = rag.answer(query, session_id)
    
    print(f"   Question: {query}")
    print(f"   Answer: {answer[:200]}...")
    
    if not answer or answer == "No relevant documents found in knowledge graph.":
        print("   ✗ No answer generated!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    # Cleanup
    print("\nCleaning up temporary files...")
    shutil.rmtree(temp_dir, ignore_errors=True)
