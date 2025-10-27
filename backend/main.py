#!/usr/bin/env python3
"""
MotherHen - Unified Application
Combines Web Scraper, Video Compressor, and Video Downloader
"""

import os
import sys
import threading
import webbrowser
import time
import tempfile
import shutil
import uuid
import glob
from pathlib import Path

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Add module paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

class MotherHenApp:
    def __init__(self):
        self.app = Flask(__name__, static_folder='../build', static_url_path='/')
        CORS(self.app)
        
        # Configuration
        self.app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 1GB
        
        # Directories
        self.download_dir = Path("downloads")
        self.compressed_dir = Path("compressed") 
        self.scraped_dir = Path("modules/scraper/outputs")
        
        # Create directories
        for dir_path in [self.download_dir, self.compressed_dir, self.scraped_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Storage
        self.downloads = {}
        
        # Initialize modules
        self._init_modules()
        self._setup_routes()
    
    def _init_modules(self):
        """Initialize all three modules"""
        # Web Scraper
        try:
            from scraper.scraper import WebScraper
            from scraper.utils import is_valid_url
            self.scraper = WebScraper()
            self.is_valid_url = is_valid_url
            self.scraper_available = True
            print("✅ Web Scraper initialized")
        except Exception as e:
            print(f"❌ Web Scraper unavailable: {e}")
            self.scraper_available = False
        
        # Video Compressor
        try:
            # Add local FFmpeg to PATH
            import subprocess
            import os
            ffmpeg_path = os.path.join(os.path.dirname(__file__), 'modules', 'ffmpeg', 'bin')
            if os.path.exists(ffmpeg_path):
                os.environ['PATH'] = ffmpeg_path + os.pathsep + os.environ.get('PATH', '')
            
            # Check if FFmpeg is available
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            
            from compressor.video_compressor import VideoCompressor
            self.compressor = VideoCompressor(
                upload_dir=str(self.download_dir),
                compressed_dir=str(self.compressed_dir)
            )
            self.compressor_available = True
            print("✅ Video Compressor initialized")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Video Compressor unavailable: FFmpeg not found")
            print("   FFmpeg binary should be in backend/modules/ffmpeg/bin/")
            self.compressor_available = False
        except Exception as e:
            print(f"❌ Video Compressor unavailable: {e}")
            self.compressor_available = False
        
        # Video Downloader
        try:
            import yt_dlp
            self.downloader_available = True
            print("✅ Video Downloader initialized")
        except ImportError:
            print("❌ Video Downloader unavailable (yt-dlp not installed)")
            self.downloader_available = False
    
    def _setup_routes(self):
        """Setup all API routes"""
        # Frontend routes
        @self.app.route('/')
        def index():
            return send_from_directory('../build', 'index.html')
        
        @self.app.route('/<path:path>')
        def static_files(path):
            try:
                return send_from_directory('../build', path)
            except:
                return send_from_directory('../build', 'index.html')
        
        # Health check
        @self.app.route('/health')
        def health():
            return jsonify({
                'status': 'ok',
                'modules': {
                    'scraper': self.scraper_available,
                    'compressor': self.compressor_available,
                    'downloader': self.downloader_available
                }
            })
        
        # Web Scraper routes
        self._setup_scraper_routes()
        
        # Video Compressor routes  
        self._setup_compressor_routes()
        
        # Video Downloader routes
        self._setup_downloader_routes()
    
    def _setup_scraper_routes(self):
        """Setup web scraper routes"""
        @self.app.route('/api/scraper/scrape', methods=['POST'])
        def scrape_website():
            if not self.scraper_available:
                return jsonify({'success': False, 'error': 'Web scraper not available'}), 500
            
            data = request.get_json()
            url = data.get('url')
            format_type = data.get('format', 'json')
            
            if not url or not self.is_valid_url(url):
                return jsonify({'success': False, 'error': 'Valid URL required'}), 400
            
            try:
                result = self.scraper.scrape(url, save_as_json=(format_type == 'json'))
                
                if result['success']:
                    return jsonify({
                        'success': True,
                        'filepath': result['filepath'],
                        'filename': os.path.basename(result['filepath']),
                        'format': format_type
                    })
                else:
                    return jsonify({'success': False, 'error': result['error']}), 400
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/scraper/download/<filename>')
        def download_scraped_file(filename):
            try:
                safe_filename = secure_filename(filename)
                file_path = self.scraped_dir / safe_filename
                
                if file_path.exists():
                    return send_file(file_path, as_attachment=True)
                else:
                    return jsonify({'error': 'File not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _setup_compressor_routes(self):
        """Setup video compressor routes"""
        @self.app.route('/api/compressor/compress', methods=['POST'])
        def compress_video():
            if not self.compressor_available:
                return jsonify({'success': False, 'error': 'Video compressor not available'}), 500
            
            if 'video' not in request.files:
                return jsonify({'success': False, 'error': 'No video file provided'}), 400
            
            file = request.files['video']
            if not file.filename:
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            compression_level = request.form.get('compression_level', 'medium')
            target_size = request.form.get('target_size', type=int)
            
            temp_dir = None
            try:
                # Save uploaded file temporarily
                temp_dir = Path(tempfile.mkdtemp())
                filename = secure_filename(file.filename)
                input_path = temp_dir / filename
                file.save(input_path)
                
                # Process video
                result = self.compressor.process_video(
                    str(input_path),
                    compression_level=compression_level,
                    target_size_mb=target_size
                )
                
                return jsonify({
                    'success': True,
                    'file_id': result['file_id'],
                    'original_filename': result['original_filename'],
                    'original_size_mb': result['original_size_mb'],
                    'compressed_size_mb': result['compressed_size_mb'],
                    'compression_ratio': result['compression_ratio'],
                    'download_url': f"/api/compressor/download/{result['file_id']}"
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
            finally:
                if temp_dir and temp_dir.exists():
                    shutil.rmtree(temp_dir)
        
        @self.app.route('/api/compressor/download/<file_id>')
        def download_compressed_video(file_id):
            try:
                for file_path in self.compressed_dir.glob(f"*{file_id}*"):
                    if file_path.is_file():
                        return send_file(file_path, as_attachment=True)
                
                return jsonify({'error': 'File not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _setup_downloader_routes(self):
        """Setup video downloader routes"""
        def progress_hook(d, download_id):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    progress = int((downloaded / total) * 100)
                    self.downloads[download_id]["progress"] = progress
                    self.downloads[download_id]["status"] = "downloading"
            elif d['status'] == 'finished':
                self.downloads[download_id]["status"] = "processing"
        
        @self.app.route('/api/downloader/download', methods=['POST'])
        def download_video():
            if not self.downloader_available:
                return jsonify({'success': False, 'error': 'Video downloader not available'}), 500
            
            data = request.get_json()
            url = data.get('url')
            format_type = data.get('format', 'mp4')
            quality = data.get('quality', 'medium')
            
            if not url:
                return jsonify({'success': False, 'error': 'URL required'}), 400
            
            try:
                import yt_dlp
                
                download_id = str(uuid.uuid4())
                self.downloads[download_id] = {
                    "id": download_id,
                    "_id": download_id,
                    "url": url,
                    "status": "starting",
                    "progress": 0,
                    "format": format_type,
                    "quality": quality
                }
                
                # Build yt_dlp options
                ydl_opts = {
                    'outtmpl': f'{self.download_dir}/{download_id}.%(ext)s',
                    'noplaylist': True,
                    'quiet': False,
                    'progress_hooks': [lambda d: progress_hook(d, download_id)],
                    'socket_timeout': 30,
                    'nocheckcertificate': True,
                    'geo_bypass': True,
                    'retries': 5,
                }
                
                # Format settings
                if format_type == "mp3":
                    quality_map = {"low": "128", "medium": "192", "high": "320"}
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': quality_map.get(quality, "192"),
                        }],
                    })
                else:
                    quality_formats = {
                        "high": 'best[ext=mp4]/best',
                        "medium": 'best[height<=720][ext=mp4]/best[height<=720]',
                        "low": 'best[height<=480][ext=mp4]/best[height<=480]'
                    }
                    ydl_opts['format'] = quality_formats.get(quality, quality_formats["medium"])
                
                # TikTok watermark removal
                if "tiktok.com" in url:
                    ydl_opts.update({
                        'format': 'best[format_id*=nowm]/best',
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                            'Referer': 'https://www.tiktok.com/'
                        }
                    })
                
                # Download in background
                def download_thread():
                    try:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            self.downloads[download_id]["status"] = "completed"
                            self.downloads[download_id]["title"] = info.get('title', 'Unknown')
                            self.downloads[download_id]["duration"] = info.get('duration', 0)
                            
                            # Get file size
                            files = list(self.download_dir.glob(f"{download_id}.*"))
                            if files:
                                self.downloads[download_id]["fileSize"] = files[0].stat().st_size
                    except Exception as e:
                        self.downloads[download_id]["status"] = "failed"
                        self.downloads[download_id]["errorMessage"] = str(e)
                
                thread = threading.Thread(target=download_thread)
                thread.daemon = True
                thread.start()
                
                return jsonify({'success': True, 'download_id': download_id})
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/downloader/downloads', methods=['GET'])
        def get_downloads():
            return jsonify(list(self.downloads.values()))
        
        @self.app.route('/api/downloader/downloads/<download_id>', methods=['DELETE'])
        def delete_download(download_id):
            if download_id in self.downloads:
                # Delete files
                for file_path in self.download_dir.glob(f"{download_id}.*"):
                    try:
                        file_path.unlink()
                    except:
                        pass
                
                del self.downloads[download_id]
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Download not found'}), 404
        
        @self.app.route('/api/downloader/download/<download_id>')
        def download_file(download_id):
            try:
                files = list(self.download_dir.glob(f"{download_id}.*"))
                if files:
                    return send_file(files[0], as_attachment=True)
                else:
                    return jsonify({'error': 'File not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the application"""
        self.app.run(host=host, port=port, debug=debug, use_reloader=False)

def open_browser(port=5000):
    """Open browser after delay"""
    time.sleep(2)
    webbrowser.open(f'http://127.0.0.1:{port}')

def main():
    print("=" * 70)
    print("                    MOTHERHEN")
    print("     Web Scraper | Video Compressor | Video Downloader")
    print("=" * 70)
    
    # Create application
    app = MotherHenApp()
    
    port = 5000
    print(f"\n🚀 Starting MotherHen server...")
    print(f"📍 Server: http://127.0.0.1:{port}")
    print("⏹️  Press Ctrl+C to stop\n")
    
    # Start browser
    browser_thread = threading.Thread(target=open_browser, args=(port,))
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        app.run(host='127.0.0.1', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n\n👋 MotherHen stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()