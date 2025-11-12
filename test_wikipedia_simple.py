#!/usr/bin/env python3
"""
Simple test script to debug Wikipedia crawling
"""
import sys
sys.path.insert(0, '/home/hydenix/repos/Arabella')

from crawler import crawl_relations

print("Testing Wikipedia crawler...")
print("-" * 60)

url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
print(f"Crawling: {url}")
print()

try:
    link_text_map, relations = crawl_relations(url, max_depth=1, use_selenium=False)
    
    print(f"✓ Crawled {len(link_text_map)} pages")
    print(f"✓ Found {len(relations)} relationships")
    print()
    
    if link_text_map:
        print("Sample URLs:")
        for i, url in enumerate(list(link_text_map.keys())[:5], 1):
            print(f"  {i}. {url}")
            text_preview = link_text_map[url][:100].replace('\n', ' ')
            print(f"     Preview: {text_preview}...")
        print()
    
    if relations:
        print(f"Sample relationships:")
        for i, (parent, child) in enumerate(relations[:3], 1):
            print(f"  {i}. {parent} -> {child}")
    
    print()
    print("✓ Test completed successfully!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
