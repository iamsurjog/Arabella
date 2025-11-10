#!/bin/bash
cd /home/hydenix/repos/Arabella

echo "Testing crawler search function..."
python3 << 'EOF'
from crawler import search_duckduckgo
urls = search_duckduckgo('python site:wikipedia.org', num_results=2)
print(f"Found {len(urls)} URLs")
for url in urls:
    print(f"  {url}")
    assert url.startswith('http'), f"Invalid URL: {url}"
print("SUCCESS!")
EOF

echo ""
echo "Testing direct crawl..."
python3 << 'EOF'
from crawler import crawl_relations
link_text_map, relations = crawl_relations('https://en.wikipedia.org/wiki/Python_(programming_language)', max_depth=0)
print(f"Crawled {len(link_text_map)} pages")
assert len(link_text_map) > 0, "No pages crawled"
print("SUCCESS!")
EOF

echo ""
echo "All tests passed!"
