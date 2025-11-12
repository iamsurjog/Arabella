"""
Selenium-based web crawler for JavaScript-heavy websites
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import Tuple, Set, Optional


class SeleniumCrawler:
    """Selenium-based web crawler for dynamic content"""
    
    def __init__(self, headless: bool = True, timeout: int = 10):
        """
        Initialize Selenium crawler
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in seconds
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
    
    def _init_driver(self):
        """Initialize Chrome WebDriver with options"""
        if self.driver is not None:
            return
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Disable automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Chrome WebDriver: {e}")
    
    def get_page(self, url: str, wait_for_selector: Optional[str] = None) -> Tuple[str, str]:
        """
        Get page HTML and text using Selenium
        
        Args:
            url: URL to fetch
            wait_for_selector: Optional CSS selector to wait for before returning
            
        Returns:
            Tuple of (html_content, page_text)
        """
        self._init_driver()
        
        try:
            self.driver.get(url)
            
            # Wait for specific element if requested
            if wait_for_selector:
                try:
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                    )
                except TimeoutException:
                    print(f"Timeout waiting for selector: {wait_for_selector}")
            else:
                # Default wait for body to load
                time.sleep(2)  # Give dynamic content time to load
            
            html_content = self.driver.page_source
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
            return html_content, page_text
            
        except TimeoutException:
            raise TimeoutException(f"Timeout loading page: {url}")
        except WebDriverException as e:
            raise WebDriverException(f"WebDriver error loading {url}: {e}")
        except Exception as e:
            raise Exception(f"Error loading {url}: {e}")
    
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
        """Close the browser and clean up resources"""
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error closing driver: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False


def get_plain_text_selenium(html: str) -> str:
    """
    Extract plain text from HTML (Selenium-compatible version)
    
    Args:
        html: HTML content
        
    Returns:
        Plain text content
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=' ', strip=True)
    return text
