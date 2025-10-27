import time
import random
import logging
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/scraper.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def get_random_delay(min_delay=1, max_delay=3):
    """Get random delay between requests"""
    return random.uniform(min_delay, max_delay)

def is_valid_url(url):
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_domain_from_url(url):
    """Extract domain from URL"""
    return urlparse(url).netloc

def generate_filename(url, extension='txt'):
    """Generate a safe filename from URL"""
    domain = get_domain_from_url(url)
    path = urlparse(url).path.strip('/')
    
    if path:
        # Replace slashes and special characters
        safe_path = path.replace('/', '_').replace('?', '_').replace('=', '_')
        filename = f"{domain}_{safe_path}.{extension}"
    else:
        filename = f"{domain}_homepage.{extension}"
    
    # Limit filename length
    if len(filename) > 100:
        filename = filename[:100] + f".{extension}"
    
    return filename

def get_random_headers():
    """Generate random headers to avoid detection"""
    ua = UserAgent()
    return {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }