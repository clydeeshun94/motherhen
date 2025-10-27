from bs4 import BeautifulSoup
import re
from .config.settings import TEXT_TAGS, REMOVE_TAGS

class ContentParser:
    def __init__(self):
        self.text_tags = TEXT_TAGS
        self.remove_tags = REMOVE_TAGS
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def extract_main_content(self, soup):
        """Extract main content from the page"""
        # Remove unwanted elements
        for tag in self.remove_tags:
            for element in soup.find_all(tag):
                element.decompose()
        
        # Try to find main content areas
        content_selectors = [
            'main', 
            'article',
            '.content',
            '.main-content',
            '#content',
            '.post-content',
            '.entry-content',
            '[role="main"]'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body') or soup
        
        return main_content
    
    def parse_html(self, html_content, url):
        """Parse HTML and extract structured content"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract title
        title = self.extract_title(soup)
        
        # Extract main content
        main_content = self.extract_main_content(soup)
        
        # Extract all text content
        text_content = self.extract_text_content(main_content)
        
        # Extract metadata
        metadata = self.extract_metadata(soup, url)
        
        return {
            'title': title,
            'url': url,
            'content': text_content,
            'metadata': metadata
        }
    
    def extract_title(self, soup):
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return self.clean_text(title_tag.get_text())
        
        # Try h1 if no title tag
        h1_tag = soup.find('h1')
        if h1_tag:
            return self.clean_text(h1_tag.get_text())
        
        return "No Title Found"
    
    def extract_text_content(self, element):
        """Extract and structure text content"""
        sections = []
        
        # Extract headings and their following content
        current_section = {'heading': 'Main Content', 'content': []}
        
        for tag in element.find_all(True):  # True matches all tags
            if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Save previous section
                if current_section['content']:
                    sections.append(current_section.copy())
                
                # Start new section
                current_section = {
                    'heading': self.clean_text(tag.get_text()),
                    'content': []
                }
            elif tag.name in ['p', 'li']:
                text = self.clean_text(tag.get_text())
                if text and len(text) > 10:  # Only include substantial text
                    current_section['content'].append(text)
        
        # Add the last section
        if current_section['content']:
            sections.append(current_section)
        
        return sections
    
    def extract_metadata(self, soup, url):
        """Extract metadata from the page"""
        metadata = {}
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata['description'] = meta_desc.get('content', '')
        
        # Keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            metadata['keywords'] = meta_keywords.get('content', '')
        
        # Open Graph data
        og_title = soup.find('meta', property='og:title')
        if og_title:
            metadata['og_title'] = og_title.get('content', '')
        
        og_description = soup.find('meta', property='og:description')
        if og_description:
            metadata['og_description'] = og_description.get('content', '')
        
        return metadata