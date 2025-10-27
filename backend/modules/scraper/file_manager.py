import json
from pathlib import Path
from datetime import datetime
from .config.settings import OUTPUT_DIR
from .utils import generate_filename

class FileManager:
    def __init__(self, output_dir=OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_as_text(self, data, filename=None):
        """Save scraped data as text file"""
        if not filename:
            filename = generate_filename(data['url'])
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"URL: {data['url']}\n")
                f.write(f"Title: {data['title']}\n")
                f.write(f"Scraped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                # Write metadata
                if data['metadata']:
                    f.write("METADATA:\n")
                    for key, value in data['metadata'].items():
                        if value:
                            f.write(f"{key}: {value}\n")
                    f.write("\n" + "=" * 80 + "\n\n")
                
                # Write content
                for section in data['content']:
                    f.write(f"{section['heading'].upper()}\n")
                    f.write("-" * len(section['heading']) + "\n\n")
                    
                    for paragraph in section['content']:
                        f.write(f"{paragraph}\n\n")
                    
                    f.write("\n")
            
            return str(filepath)
        
        except Exception as e:
            raise Exception(f"Error saving file: {str(e)}")
    
    def save_as_json(self, data, filename=None):
        """Save scraped data as JSON file"""
        if not filename:
            filename = generate_filename(data['url'], 'json')
        
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return str(filepath)
        
        except Exception as e:
            raise Exception(f"Error saving JSON file: {str(e)}")
    
    def get_file_info(self, filepath):
        """Get information about saved file"""
        path = Path(filepath)
        if path.exists():
            return {
                'filename': path.name,
                'filepath': str(path),
                'size': path.stat().st_size,
                'created': datetime.fromtimestamp(path.stat().st_ctime)
            }
        return None