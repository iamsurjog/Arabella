#!/usr/bin/env python3
"""Quick test of crawler functionality"""

from crawler import search_duckduckgo, crawl_relations, is_url

def test_search():
    print("Testing search_duckduckgo...")
    urls = search_duckduckgo('python programming site:wikipedia.org', num_results=2)
    print(f"Found {len(urls)} URLs:")
    for url in urls:
        print(f"  - {url}")
        assert is_url(url), f"Invalid URL: {url}"
    print("✓ Search test passed\n")
    return urls

def test_direct_crawl():
    print("Testing direct URL crawl...")
    url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    link_text_map, relations = crawl_relations(url, max_depth=0)
    print(f"Crawled {len(link_text_map)} pages")
    print(f"Found {len(relations)} relationships")
    assert len(link_text_map) > 0, "No pages crawled"
    
    sample_url = list(link_text_map.keys())[0]
    sample_text = link_text_map[sample_url]
    print(f"Sample URL: {sample_url}")
    print(f"Text length: {len(sample_text)} characters")
    print(f"Sample text: {sample_text[:200]}")
    print("✓ Direct crawl test passed\n")
    return link_text_map, relations

def test_search_crawl():
    print("Testing search + crawl...")
    link_text_map, relations = crawl_relations(
        'python programming language site:wikipedia.org',
        max_depth=0
    )
    print(f"Crawled {len(link_text_map)} pages")
    print(f"Found {len(relations)} relationships")
    
    if len(link_text_map) > 0:
        print("✓ Search + crawl test passed")
    else:
        print("⚠ Warning: No pages crawled from search")
    return link_text_map, relations

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("CRAWLER TESTS")
        print("=" * 60 + "\n")
        
        # Test 1: Search function
        urls = test_search()
        
        # Test 2: Direct crawl
        link_text_map, relations = test_direct_crawl()
        
        # Test 3: Search + crawl
        link_text_map2, relations2 = test_search_crawl()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
