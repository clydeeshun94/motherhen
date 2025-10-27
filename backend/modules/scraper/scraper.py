import requests
from requests.exceptions import RequestException, Timeout, TooManyRedirects
import time
from .content_parser import ContentParser
from .file_manager import FileManager
from .utils import setup_logging, get_random_delay, is_valid_url, get_random_headers
from .config.settings import DEFAULT_HEADERS, REQUEST_TIMEOUT, MAX_RETRIES, DELAY_BETWEEN_REQUESTS

class WebScraper:
    def __init__(self, delay=DELAY_BETWEEN_REQUESTS, max_retries=MAX_RETRIES):
        self.logger = setup_logging()
        self.parser = ContentParser()
        self.file_manager = FileManager()
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
    
    def fetch_url(self, url):
        """Fetch content from URL with error handling and retries"""
        if not is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Fetching URL: {url} (Attempt {attempt + 1})")
                
                # Use random headers for each request
                headers = get_random_headers()
                
                response = self.session.get(
                    url, 
                    timeout=REQUEST_TIMEOUT,
                    headers=headers,
                    allow_redirects=True
                )
                
                response.raise_for_status()
                
                self.logger.info(f"Successfully fetched URL: {url}")
                return response.text
                
            except Timeout:
                self.logger.warning(f"Timeout occurred for {url} (Attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Timeout after {self.max_retries} attempts")
                    
            except TooManyRedirects:
                self.logger.error(f"Too many redirects for {url}")
                raise Exception("Too many redirects")
                
            except RequestException as e:
                self.logger.error(f"Request failed for {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Request failed after {self.max_retries} attempts: {str(e)}")
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                delay = get_random_delay(self.delay, self.delay * 2)
                self.logger.info(f"Waiting {delay:.2f} seconds before retry...")
                time.sleep(delay)
        
        raise Exception(f"Failed to fetch {url} after {self.max_retries} attempts")
    
    def scrape(self, url, save_as_json=False):
        """Main method to scrape URL and save content"""
        try:
            # Fetch HTML content
            html_content = self.fetch_url(url)
            
            # Parse content
            parsed_data = self.parser.parse_html(html_content, url)
            
            # Save to file
            if save_as_json:
                filepath = self.file_manager.save_as_json(parsed_data)
            else:
                filepath = self.file_manager.save_as_text(parsed_data)
            
            # Get file info
            file_info = self.file_manager.get_file_info(filepath)
            
            self.logger.info(f"Successfully scraped and saved: {filepath}")
            
            return {
                'success': True,
                'url': url,
                'filepath': filepath,
                'file_info': file_info,
                'data': parsed_data
            }
            
        except Exception as e:
            self.logger.error(f"Scraping failed for {url}: {str(e)}")
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'filepath': None
            }
    
    def scrape_multiple(self, urls, save_as_json=False):
        """Scrape multiple URLs"""
        results = []
        for url in urls:
            result = self.scrape(url, save_as_json)
            results.append(result)
            
            # Respectful delay between requests
            if len(urls) > 1:
                delay = get_random_delay(self.delay, self.delay * 2)
                self.logger.info(f"Waiting {delay:.2f} seconds before next request...")
                time.sleep(delay)
        
        return results