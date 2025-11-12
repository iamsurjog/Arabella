"""
Simple requests-based web crawler for static content
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, Tuple


class RequestsCrawler:
    """Simple requests-based crawler for static content"""
    
    def __init__(self, timeout: int = 10):
        """
        Initialize requests crawler
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_page(self, url: str) -> Tuple[str, str]:
        """
        Get page HTML and text using requests
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (html_content, page_text)
        """
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            html = resp.text
            
            # Extract plain text
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            plain_text = soup.get_text(separator=' ', strip=True)
            
            return html, plain_text
            
        except requests.RequestException as e:
            raise Exception(f"Error fetching {url}: {e}")
    
    def extract_links(self, base_url: str, html: str) -> Set[str]:
        """
        Extract links from HTML content
        
        Args:
            base_url: Base URL for resolving relative links
            html: HTML content
            
        Returns:
            Set of absolute URLs
        """
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get("href")
            url = urljoin(base_url, href)
            if urlparse(url).scheme in ["http", "https"]:
                links.add(url)
        
        return links
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False
