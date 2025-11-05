import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_plain_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]): tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return text

def extract_links(base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        url = urljoin(base_url, href)
        if urlparse(url).scheme in ["http", "https"]:
            links.add(url)
    return links

def crawl_relations(url, max_depth=2):
    visited = set()
    link_text_map = dict()
    relations = []

    def _crawl(current_url, depth, parent=None):
        if depth > max_depth or current_url in visited:
            return
        try:
            resp = requests.get(current_url, timeout=10)
            resp.raise_for_status()
            html = resp.text
            plain_text = get_plain_text(html)
            link_text_map[current_url] = plain_text
            visited.add(current_url)
            if parent is not None:
                relations.append((parent, current_url))
            if depth < max_depth:
                links = extract_links(current_url, html)
                for link in links:
                    _crawl(link, depth + 1, current_url)
        except Exception:
            pass  # skip broken

    _crawl(url, 0, None)
    return [link_text_map, relations]

# Usage:
if __name__ == "__main__":
    start_url = "http://127.0.0.1:5000"
    results = crawl_relations(start_url, max_depth=2)
    # Output: [{'link1': 'text1', ...}, [(link1, link2), ...]]
    print(results)
