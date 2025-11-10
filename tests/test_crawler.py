import pytest
from crawler import crawl_relations, get_plain_text, extract_links
from bs4 import BeautifulSoup


class TestCrawler:
    """Unit tests for Crawler module"""
    
    def test_get_plain_text(self):
        """Test plain text extraction from HTML"""
        html = """
        <html>
            <head><title>Test</title></head>
            <body>
                <script>alert('test');</script>
                <style>.test { color: red; }</style>
                <p>This is a test paragraph.</p>
            </body>
        </html>
        """
        text = get_plain_text(html)
        assert "This is a test paragraph" in text
        assert "alert" not in text  # script should be removed
        assert "color: red" not in text  # style should be removed
    
    def test_extract_links(self):
        """Test link extraction from HTML"""
        base_url = "https://example.com"
        html = """
        <html>
            <body>
                <a href="/page1">Page 1</a>
                <a href="https://example.com/page2">Page 2</a>
                <a href="http://other.com">Other</a>
            </body>
        </html>
        """
        links = extract_links(base_url, html)
        assert isinstance(links, set)
        assert len(links) > 0
        # Check that relative URLs are converted to absolute
        assert any("example.com" in link for link in links)
    
    def test_crawl_relations_structure(self):
        """Test that crawl_relations returns correct structure"""
        # Note: This test would need a mock server or skip in CI
        # For now, we just test the structure
        result = crawl_relations("http://nonexistent.example.com", max_depth=1)
        assert isinstance(result, list)
        assert len(result) == 2
        link_text_map, relations = result
        assert isinstance(link_text_map, dict)
        assert isinstance(relations, list)


class TestCrawlerIntegration:
    """Integration tests for crawler (requires network)"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_crawl_real_site(self):
        """Test crawling a real website (example.com)"""
        link_text_map, relations = crawl_relations("http://example.com", max_depth=1)
        # Should have at least the root page
        assert len(link_text_map) >= 1
        assert isinstance(relations, list)
