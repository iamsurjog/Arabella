from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import pickle
import re


def extract_urls(html, base_url, domain):
    # Regex to match http/https URLs
    url_regex = r'http[s]?://[^\s"\'<>]+'
    urls = set(re.findall(url_regex, html))
    
    # Also find relative URLs in href/src attributes
    attr_regex = r'(?:href|src)\s*=\s*[\'"]([^\'"]+)[\'"]'
    rel_urls = re.findall(attr_regex, html)
    for rel_url in rel_urls:
        abs_url = urljoin(base_url, rel_url)
        urls.add(abs_url)
    
    # Filter for domain
    filtered = {u for u in urls if domain in urlparse(u).netloc and "jpg" not in u}
    return filtered


def fetch_html_css_js(url, domain, visited=None):
    if visited is None:
        visited = {}
    
    if url in visited:
        return visited
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        html = response.text
    except requests.RequestException:
        return visited
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract CSS from <link> tags and inline <style> tags
    styles = ''
    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href')
        if href:
            css_url = urljoin(url, href)
            try:
                css_response = requests.get(css_url)
                css_response.raise_for_status()
                styles += f"<style>{css_response.text}</style>"
            except requests.RequestException:
                continue
    for style in soup.find_all('style'):
        styles += f"<style>{style.string if style.string else ''}</style>"
    
    # Extract JS from <script> tags
    scripts = ''
    for script in soup.find_all('script'):
        src = script.get('src')
        if src:
            js_url = urljoin(url, src)
            try:
                js_response = requests.get(js_url)
                js_response.raise_for_status()
                scripts += f"<script>{js_response.text}</script>"
            except requests.RequestException:
                continue
        else:
            scripts += f"<script>{script.string if script.string else ''}</script>"
    
    # Combine HTML body with styles and scripts
    body = soup.body
    combined = ''
    if body:
        combined = str(body) + styles + scripts
    else:
        combined = html + styles + scripts
    
    visited[url] = combined
    print(f"{url} visited")
    # print(combined)
    # Recursively process links with the specified domain
    found_urls = extract_urls(html, url, domain)
    # print(found_urls)
    for found_url in found_urls:
        if found_url not in visited:
            fetch_html_css_js(found_url, domain, visited)    
    return visited


def clean_website_content(scraped_data):
    """
    Takes a dictionary of {url: html_content} and returns {url: plain_text}
    """
    cleaned_data = {}

    for url, html in scraped_data.items():
        soup = BeautifulSoup(html, "html.parser")

        # Remove <script> and <style> tags along with their content
        for tag in soup(["script", "style"]):
            tag.decompose()

        # Get text, strip leading/trailing spaces and normalize spacing
        text = soup.get_text(separator=' ', strip=True)
        cleaned_text = ' '.join(text.split())  # Normalize whitespace

        cleaned_data[url] = cleaned_text

    return cleaned_data


scraped_sites = fetch_html_css_js('https://www.mosdac.gov.in/', 'mosdac.gov.in/')

f = open("sites.dat", "wb")
pickle.dump(scraped_sites)
f.close()

cleaned_output = clean_website_content(scraped_sites)

f = open("sites_cleaned.dat", "wb")
pickle.dump(cleaned_output)
f.close()



# Print result
# for url, content in cleaned_output.items():
#     print(f"URL: {url}\nContent: {content}\n")
