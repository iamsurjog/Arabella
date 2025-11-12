"""
Wikipedia-specific crawler optimized for Wikipedia content
"""
from .selenium_crawler import SeleniumCrawler
from .requests_crawler import RequestsCrawler
from typing import Tuple, Set, Dict, List
import re


class WikipediaCrawler:
    """Specialized crawler for Wikipedia that handles its structure efficiently"""
    
    def __init__(self, use_selenium: bool = False, timeout: int = 10):
        """
        Initialize Wikipedia crawler
        
        Args:
            use_selenium: Use Selenium for crawling (slower but more robust)
            timeout: Request timeout in seconds
        """
        self.use_selenium = use_selenium
        self.timeout = timeout
        
        if use_selenium:
            self.crawler = SeleniumCrawler(headless=True, timeout=timeout)
        else:
            self.crawler = RequestsCrawler(timeout=timeout)
    
    def is_wikipedia_url(self, url: str) -> bool:
        """Check if URL is a Wikipedia page"""
        return 'wikipedia.org/wiki/' in url
    
    def filter_wikipedia_links(self, links: Set[str], base_url: str) -> Set[str]:
        """
        Filter links to keep only relevant Wikipedia pages
        
        Args:
            links: Set of URLs to filter
            base_url: Base URL for context
            
        Returns:
            Filtered set of Wikipedia URLs
        """
        filtered = set()
        
        for link in links:
            # Only keep Wikipedia article pages
            if not self.is_wikipedia_url(link):
                continue
            
            # Skip special pages, files, help pages, etc.
            skip_patterns = [
                'wikipedia.org/wiki/Special:',
                'wikipedia.org/wiki/File:',
                'wikipedia.org/wiki/Help:',
                'wikipedia.org/wiki/Wikipedia:',
                'wikipedia.org/wiki/Talk:',
                'wikipedia.org/wiki/Category:',
                'wikipedia.org/wiki/Portal:',
                'wikipedia.org/wiki/Template:',
                '#',  # Skip anchor links
            ]
            
            if any(pattern in link for pattern in skip_patterns):
                continue
            
            # Skip links to other language Wikipedias
            if re.search(r'//[a-z]{2}\.wikipedia\.org', link):
                # Check if it's the same language as base_url
                base_lang = re.search(r'//([a-z]{2})\.wikipedia\.org', base_url)
                link_lang = re.search(r'//([a-z]{2})\.wikipedia\.org', link)
                if base_lang and link_lang and base_lang.group(1) != link_lang.group(1):
                    continue
            
            filtered.add(link)
        
        return filtered
    
    def crawl(self, url: str, max_depth: int = 2, max_pages: int = 20) -> Tuple[Dict[str, str], List[Tuple[str, str]]]:
        """
        Crawl Wikipedia pages starting from a URL
        
        Args:
            url: Starting Wikipedia URL
            max_depth: Maximum depth to crawl
            max_pages: Maximum number of pages to crawl
            
        Returns:
            Tuple of (link_text_map, relations)
        """
        visited = set()
        link_text_map = {}
        relations = []
        pages_crawled = 0
        
        def _crawl(current_url: str, depth: int, parent: str = None):
            nonlocal pages_crawled
            
            if depth > max_depth or current_url in visited or pages_crawled >= max_pages:
                return
            
            if not self.is_wikipedia_url(current_url):
                return
            
            try:
                # Get page content
                html, plain_text = self.crawler.get_page(current_url)
                
                link_text_map[current_url] = plain_text
                visited.add(current_url)
                pages_crawled += 1
                
                if parent is not None:
                    relations.append((parent, current_url))
                
                print(f"Crawled ({pages_crawled}/{max_pages}): {current_url}")
                
                # Extract and filter links
                if depth < max_depth and pages_crawled < max_pages:
                    links = self.crawler.extract_links(current_url, html)
                    wikipedia_links = self.filter_wikipedia_links(links, current_url)
                    
                    # Limit to first 5 links per page to avoid explosion
                    for link in list(wikipedia_links)[:5]:
                        _crawl(link, depth + 1, current_url)
                        
            except Exception as e:
                print(f"Error crawling {current_url}: {e}")
        
        # Start crawling
        _crawl(url, 0)
        
        return link_text_map, relations
    
    def close(self):
        """Close the underlying crawler"""
        if hasattr(self.crawler, 'close'):
            self.crawler.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False
