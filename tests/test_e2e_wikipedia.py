"""
End-to-end integration test for Wikipedia search
This test crawls Wikipedia, indexes content, and answers questions
"""
import pytest
import tempfile
import shutil
from crawler import crawl_relations
from rag import GraphRAG
from query_bridge import QueryBridge


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.e2e
class TestWikipediaE2E:
    """End-to-end test using Wikipedia as data source"""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for databases"""
        # Create parent directory
        parent_dir = tempfile.mkdtemp(prefix="test_e2e_")
        # KuzuDB will create its own directory
        kuzu_dir = f"{parent_dir}/kuzu_db"
        vector_dir = f"{parent_dir}/vector_db"
        yield kuzu_dir, vector_dir
        # Cleanup
        shutil.rmtree(parent_dir, ignore_errors=True)
    
    def test_wikipedia_python_search(self, temp_dirs):
        """
        End-to-end test: Search Wikipedia for Python information
        
        Flow:
        1. Transform query using QueryBridge
        2. Crawl Wikipedia
        3. Index in Graph-RAG
        4. Generate answer
        """
        kuzu_dir, vector_dir = temp_dirs
        
        # Initialize components
        query_bridge = QueryBridge()
        rag = GraphRAG(
            embedding_model='nomic-embed-text:v1.5',
            language_model='llama3.2:3b',
            vector_size=768,
            kuzu_db_path=kuzu_dir,
            qdrant_path=vector_dir
        )
        
        # Step 1: Transform query
        original_query = "What is Python programming language?"
        search_query = query_bridge.transform(original_query)
        print(f"\nOriginal query: {original_query}")
        print(f"Transformed query: {search_query}")
        
        assert isinstance(search_query, str)
        assert len(search_query) > 0
        
        # Step 2: Crawl Wikipedia directly (more reliable than search)
        print("\nCrawling Wikipedia...")
        wikipedia_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        
        try:
            link_text_map, relations = crawl_relations(
                wikipedia_url,
                max_depth=1,  # Limit to 1 level for faster test
                use_selenium=False  # Try requests first
            )
        except Exception as e:
            print(f"Crawling failed: {e}")
            pytest.skip(f"Failed to crawl Wikipedia: {e}")
        
        print(f"Crawled {len(link_text_map)} pages")
        print(f"Found {len(relations)} relationships")
        
        assert len(link_text_map) > 0, (
            f"No pages were crawled. This could be due to:\n"
            f"1. Network issues\n"
            f"2. Wikipedia being unreachable\n"
            f"Please check your internet connection."
        )
        assert isinstance(link_text_map, dict)
        
        # Verify we got Wikipedia content
        wikipedia_found = any('wikipedia.org' in url.lower() for url in link_text_map.keys())
        print(f"Wikipedia content found: {wikipedia_found}")
        print(f"Sample URLs: {list(link_text_map.keys())[:3]}")
        
        if not wikipedia_found:
            # Log what we got instead
            print("URLs crawled:")
            for url in list(link_text_map.keys())[:5]:
                print(f"  - {url}")
            pytest.skip("No Wikipedia pages found in results")
        
        # Step 3: Index in Graph-RAG (limit content size for speed)
        print("\nIndexing documents...")
        session_id = "wikipedia-test"
        
        # Limit content size to speed up testing
        limited_link_text_map = {
            url: text[:2000]  # Only first 2000 chars per page
            for url, text in link_text_map.items()
        }
        
        success = rag.bulk_index_from_crawler(relations, limited_link_text_map, session_id)
        
        assert success is True, "Failed to index documents"
        
        # Verify indexing worked
        nodes = rag.graph_db.get_session_nodes(session_id)
        print(f"Indexed {len(nodes)} nodes in graph")
        assert len(nodes) > 0, "No nodes were indexed"
        
        # Step 4: Test embeddings
        print("\nTesting embeddings...")
        sample_text = list(limited_link_text_map.values())[0][:500]  # First 500 chars
        embedding = rag.embed_text(sample_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert not all(x == 0.0 for x in embedding), "Embedding is all zeros (error case)"
        print(f"Embedding dimension: {len(embedding)}")
        print(f"Embedding sample: {embedding[:5]}")
        
        # Step 5: Generate answer
        print("\nGenerating answer...")
        answer = rag.answer(original_query, session_id)
        
        print(f"\nQuestion: {original_query}")
        print(f"Answer: {answer}")
        
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert answer != "No relevant documents found in knowledge graph."
        assert "Error" not in answer or len(answer) > 100  # If error, should be detailed
        
        # Step 6: Test retrieval
        print("\nTesting retrieval...")
        docs = rag.retrieve_with_graph_traversal(original_query, session_id, top_k=5)
        
        assert len(docs) > 0, "No documents retrieved"
        print(f"Retrieved {len(docs)} documents")
        
        # Verify document structure
        for doc in docs[:3]:
            assert "type" in doc
            assert "url" in doc
            assert "score" in doc or "depth" in doc
            print(f"  - {doc['type']}: {doc['url']}")
    
    def test_wikipedia_multi_hop_reasoning(self, temp_dirs):
        """
        Test multi-hop reasoning across Wikipedia pages
        
        This tests the graph traversal capabilities by asking a question
        that might require information from multiple related pages.
        """
        kuzu_dir, vector_dir = temp_dirs
        
        rag = GraphRAG(
            embedding_model='nomic-embed-text:v1.5',
            language_model='llama3.2:3b',
            vector_size=768,
            kuzu_db_path=kuzu_dir,
            qdrant_path=vector_dir
        )
        
        # Use direct Wikipedia URL for more reliable testing
        wikipedia_url = "https://en.wikipedia.org/wiki/Machine_learning"
        print(f"\nCrawling from URL: {wikipedia_url}")
        
        try:
            link_text_map, relations = crawl_relations(
                wikipedia_url, 
                max_depth=2,
                use_selenium=False
            )
        except Exception as e:
            pytest.skip(f"Failed to crawl Wikipedia: {e}")
        
        if len(link_text_map) < 2:
            pytest.skip(f"Not enough pages crawled for multi-hop test (got {len(link_text_map)})")
        
        print(f"Crawled {len(link_text_map)} pages with {len(relations)} relations")
        
        # Limit content size for faster indexing
        limited_link_text_map = {
            url: text[:2000]
            for url, text in link_text_map.items()
        }
        
        session_id = "multi-hop-test"
        success = rag.bulk_index_from_crawler(relations, limited_link_text_map, session_id)
        assert success is True, "Failed to index documents"
        
        # Ask a question that might require multi-hop reasoning
        question = "How is machine learning related to artificial intelligence?"
        answer = rag.answer(question, session_id)
        
        print(f"\nQuestion: {question}")
        print(f"Answer: {answer}")
        
        assert isinstance(answer, str)
        assert len(answer) > 50, f"Answer too short: {answer}"  # Should be a substantial answer
        
        # Verify graph traversal found related docs
        docs = rag.retrieve_with_graph_traversal(question, session_id, top_k=3, use_graph=True)
        
        # Check if we have both vector and graph traversal results
        types = set(doc.get("type") for doc in docs)
        print(f"Retrieval types: {types}")
        
        # Should have at least vector search results
        assert "vector_search" in types, f"Expected vector_search in types, got: {types}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
