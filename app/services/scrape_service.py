import os
import re
import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from urllib.parse import urlparse
from app.core.logger import logger
from app.database.manager import db

class ScrapeService:
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            # Default to course-ai/data/scraped
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "data", "scraped"))
        else:
            self.output_dir = output_dir
            
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"ScrapeService initialized. Saving results to: {self.output_dir}")

    def _url_to_filename(self, url: str) -> str:
        parsed = urlparse(url)
        # Combine domain and path, e.g., www.w3schools.com/python/python_variables
        combined = parsed.netloc + parsed.path
        # Clean non-alphanumeric characters
        filename = re.sub(r'[^a-zA-Z0-9]', '_', combined)
        filename = filename.strip('_')[:100]
        if not filename:
            filename = "scraped_content"
        return f"{filename}.md"

    def _clean_html(self, html_content: str) -> str:
        # Try trafilatura first if installed for ML-grade noise extraction
        try:
            import trafilatura
            extracted = trafilatura.extract(html_content, include_comments=False, include_tables=True, no_fallback=False)
            if extracted and len(extracted) > 200:
                return f"<div>{extracted}</div>"
        except ImportError:
            pass

        soup = BeautifulSoup(html_content, "html.parser")
        # Remove navigation, headers, footers, scripts, styling, forms, and buttons
        for tag in ["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe", "form", "svg", "canvas", "button"]:
            for match in soup.find_all(tag):
                match.decompose()
                
        # Remove common noisy class/id patterns (cookie banners, ads, sidebars, comments, social share, breadcrumbs)
        noisy_pattern = re.compile(r'(cookie|banner|ad-|ads-|sidebar|comment|social|share|breadcrumb|menu|popup|modal|newsletter|promo|sponsor)', re.I)
        for element in soup.find_all(attrs={"class": noisy_pattern}):
            element.decompose()
        for element in soup.find_all(attrs={"id": noisy_pattern}):
            element.decompose()
                
        # Locate main content container for cleaner text extraction
        main_content = soup.find("main") or soup.find("article") or soup.find("div", {"id": re.compile(r'^(main|content|article|post)$', re.I)}) or soup.find("div", {"class": re.compile(r'^(main|content|article|post|body-content)$', re.I)})
        if main_content:
            return str(main_content)
        return str(soup.body or soup)

    def scrape(self, url: str) -> str:
        logger.info(f"ScrapeService: Checking cache for URL: {url}")
        
        # Check database cache first
        cached_content = db.get_source(url)
        if cached_content:
            logger.info(f"ScrapeService: Cache HIT for URL: {url}")
            # Also write it to files as backup/sync if the file doesn't exist
            filename = self._url_to_filename(url)
            file_path = os.path.join(self.output_dir, filename)
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(cached_content)
            return cached_content
            
        logger.info(f"ScrapeService: Cache MISS. Scraping URL: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            # Fetch HTML
            response = httpx.get(url, headers=headers, follow_redirects=True, timeout=15.0)
            if response.status_code != 200:
                raise Exception(f"HTTP error {response.status_code} loading {url}")
                
            # Clean HTML
            cleaned_html = self._clean_html(response.text)
            
            # Convert to Markdown
            markdown_content = md(cleaned_html, strip=['a', 'img']).strip()
            # Collapse multiple newlines
            markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
            
            # Save to disk
            filename = self._url_to_filename(url)
            file_path = os.path.join(self.output_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
                
            # Save to database
            db.save_source(url, markdown_content)
                
            logger.info(f"ScrapeService: Successfully scraped {url} and saved markdown to {file_path}")
            return markdown_content
        except Exception as e:
            logger.error(f"ScrapeService: Failed to scrape {url}: {e}")
            raise e
