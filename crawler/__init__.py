import sys
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Import modular crawlers
from .requests_crawler import RequestsCrawler
from .selenium_crawler import SeleniumCrawler
from .wikipedia_crawler import WikipediaCrawler


def get_plain_text(html):
    """Extract plain text from HTML"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]): 
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return text


def extract_links(base_url, html):
    """Extract links from HTML"""
    from urllib.parse import urljoin
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        url = urljoin(base_url, href)
        if urlparse(url).scheme in ["http", "https"]:
            links.add(url)
    return links

def search_duckduckgo(query, num_results=5):
    """
    Search DuckDuckGo and return URLs
    
    Args:
        query: Search query string
        num_results: Number of results to return
        
    Returns:
        List of URLs
    """
    try:
        # Use DuckDuckGo HTML search (no API key needed)
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        urls = []
        
        # Extract result links
        for result in soup.find_all('a', class_='result__a', limit=num_results * 3):
            href = result.get('href')
            if not href:
                continue
                
            # Skip DuckDuckGo's own URLs (ads, navigation, etc.)
            if 'duckduckgo.com' in href and 'uddg=' not in href:
                continue
                
            # Handle DuckDuckGo wrapped URLs - extract the actual URL from uddg parameter
            if 'uddg=' in href:
                # Fix relative URLs first
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = 'https://duckduckgo.com' + href
                
                # Extract URL from uddg parameter
                try:
                    import urllib.parse
                    parsed = urllib.parse.urlparse(href)
                    params = urllib.parse.parse_qs(parsed.query)
                    if 'uddg' in params:
                        actual_url = params['uddg'][0]
                        # Fix relative URLs in the extracted URL
                        if actual_url.startswith('//'):
                            actual_url = 'https:' + actual_url
                        # Only add valid HTTP(S) URLs
                        if actual_url.startswith('http'):
                            # Skip ads and DuckDuckGo internal pages
                            if 'duckduckgo.com/y.js' not in actual_url and 'duckduckgo.com' not in actual_url:
                                urls.append(actual_url)
                except Exception as e:
                    print(f"Error parsing URL {href}: {e}")
                    continue
        
        # If no results with uddg, try finding direct links
        if not urls:
            for result in soup.find_all('a', href=True):
                href = result.get('href')
                if href and href.startswith('http') and 'duckduckgo.com' not in href:
                    urls.append(href)
                    if len(urls) >= num_results:
                        break
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls[:num_results]
    
    except Exception as e:
        print(f"Search error: {e}")
        return []

def is_url(text):
    """Check if text is a URL"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(text) is not None

def crawl_relations(query_or_url, max_depth=2, use_selenium=False):
    """
    Crawl web pages starting from a URL or search query
    
    Args:
        query_or_url: Either a URL to crawl or a search query
        max_depth: Maximum depth to crawl
        use_selenium: Use Selenium for JavaScript-heavy sites
        
    Returns:
        Tuple of (link_text_map, relations)
        - link_text_map: Dict mapping URLs to their text content
        - relations: List of (parent_url, child_url) tuples
    """
    # Check if it's a Wikipedia URL - use specialized crawler
    if is_url(query_or_url) and 'wikipedia.org' in query_or_url:
        print(f"Using Wikipedia crawler for: {query_or_url}")
        try:
            with WikipediaCrawler(use_selenium=use_selenium) as crawler:
                link_text_map, relations = crawler.crawl(
                    query_or_url, 
                    max_depth=max_depth,
                    max_pages=20
                )
                return [link_text_map, relations]
        except Exception as e:
            print(f"Wikipedia crawler error: {e}, falling back to standard crawler")
    
    # Standard crawling logic
    visited = set()
    link_text_map = dict()
    relations = []
    
    # Determine if input is URL or search query
    if is_url(query_or_url):
        start_urls = [query_or_url]
    else:
        # It's a search query - convert to Wikipedia URL if relevant
        if 'wikipedia' in query_or_url.lower() or 'site:wikipedia.org' in query_or_url:
            # Extract search terms and create Wikipedia search URL
            search_terms = query_or_url.replace('site:wikipedia.org', '').strip()
            # Use Wikipedia's search
            wikipedia_search_url = f"https://en.wikipedia.org/wiki/{search_terms.replace(' ', '_')}"
            print(f"Trying Wikipedia URL: {wikipedia_search_url}")
            start_urls = [wikipedia_search_url]
        else:
            print(f"Searching for: {query_or_url}")
            start_urls = search_duckduckgo(query_or_url, num_results=3)
            if not start_urls:
                print("No search results found")
                return [link_text_map, relations]
            print(f"Found {len(start_urls)} search results")
            for url in start_urls:
                print(f"  - {url}")

    def _crawl(current_url, depth, parent=None):
        if depth > max_depth or current_url in visited:
            return
        
        # Skip invalid URLs
        if not current_url or not is_url(current_url):
            return
            
        try:
            resp = requests.get(current_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            resp.raise_for_status()
            html = resp.text
            plain_text = get_plain_text(html)
            link_text_map[current_url] = plain_text
            visited.add(current_url)
            if parent is not None:
                relations.append((parent, current_url))
            if depth < max_depth:
                links = extract_links(current_url, html)
                # Limit child links to avoid crawling too many pages
                for link in list(links)[:10]:
                    _crawl(link, depth + 1, current_url)
        except Exception as e:
            print(f"Error crawling {current_url}: {e}")
            pass  # skip broken

    # Crawl each starting URL
    for start_url in start_urls:
        _crawl(start_url, 0, None)
    
    return [link_text_map, relations]

# Usage:
if __name__ == "__main__":
    start_url = "http://127.0.0.1:5000"
    results = crawl_relations(start_url, max_depth=2)
    # Output: [{'link1': 'text1', ...}, [(link1, link2), ...]]
    print(results)

# Export functions for module imports
__all__ = ['crawl_relations', 'get_plain_text', 'extract_links', 'search_duckduckgo', 'is_url']
