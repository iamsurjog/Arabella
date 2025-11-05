import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_plain_text(html):
    soup = BeautifulSoup(html, "html.parser")
    # Remove script and style elements
    for tag in soup(["script", "style"]):
        tag.decompose()
    # Get plain text
    text = soup.get_text(separator=' ', strip=True)
    return text

def extract_links(base_url, html):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        url = urljoin(base_url, href)
        # Only include HTTP/HTTPS links, and avoid mailto, fragments, javascript etc.
        if urlparse(url).scheme in ["http", "https"]:
            links.add(url)
    return links

def crawl(url, max_depth=2):
    visited = set()
    results = []

    def _crawl(current_url, depth):
        if depth > max_depth or current_url in visited:
            return
        try:
            resp = requests.get(current_url, timeout=10)
            resp.raise_for_status()
            html = resp.text
            plain_text = get_plain_text(html)
            results.append({'url': current_url, 'text': plain_text})
            visited.add(current_url)
            if depth < max_depth:
                links = extract_links(current_url, html)
                for link in links:
                    _crawl(link, depth + 1)
        except Exception as e:
            # Skip problematic URLs silently
            pass

    _crawl(url, 0)
    return results

# Usage example:
if __name__ == "__main__":
    seed_url = "https://example.com"
    data = crawl(seed_url, max_depth=2)
    # Each item is {'url': ..., 'text': ...}
    for item in data:
        print(f"URL: {item['url']}\nText:\n{item['text'][:500]}\n{'-'*60}\n")
