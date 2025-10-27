#!/usr/bin/env python3
"""
Main entry point for the multifunctional application:
1. Web Scraper
2. Video Compressor
3. Video Downloader
"""

import sys
import os
import webbrowser
import threading
import time
import subprocess
import glob
import uuid
import tempfile
import shutil

# Add paths to import modules from different parts of the application
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules', 'scraper'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules', 'compressor'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules', 'downloader'))

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        # Try to run ffmpeg command
        subprocess.run(['ffmpeg', '-version'], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL,
                     check=True)
        subprocess.run(['ffprobe', '-version'], 
                     stdout=subprocess.DEVNULL, 
                     stderr=subprocess.DEVNULL,
                     check=True)
        return {'installed': True}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {'installed': False, 'error': 'FFmpeg not found'}

def install_ffmpeg():
    """Try to automatically install FFmpeg"""
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'modules', 'compressor'))
        from ffmpeg_installer import install_ffmpeg_if_needed
        return install_ffmpeg_if_needed()
    except ImportError:
        return False
    except Exception as e:
        print(f"Error during FFmpeg installation: {e}")
        return False

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app)
    
    app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 1GB max file size
    
    # Download tracking
    downloads = {}
    DOWNLOAD_DIR = "downloads"
    
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    
    # Import modules
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
        from scraper.scraper import WebScraper
        from scraper.utils import is_valid_url as scraper_is_valid_url  # pyright: ignore[reportMissingImports]
        scraper_available = True
    except Exception as e:
        print(f"Warning: Web scraper not available: {e}")
        scraper_available = False
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
        from compressor.video_compressor import VideoCompressor
        video_compressor = VideoCompressor()
        compressor_available = True
    except Exception as e:
        print(f"Warning: Video compressor not available: {e}")
        video_compressor = None
        compressor_available = False
    
    try:
        import yt_dlp
        downloader_available = True
    except ImportError:
        print("Warning: Video downloader not available (yt-dlp not installed)")
        downloader_available = False
    
    def progress_hook(d, download_id):
        """Track download progress"""
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 0:
                progress = int((downloaded / total) * 100)
                downloads[download_id]["progress"] = progress
                downloads[download_id]["status"] = "downloading"
        elif d['status'] == 'finished':
            downloads[download_id]["status"] = "processing"
    
    # Routes for Web Scraper
    @app.route('/api/scraper/scrape', methods=['POST'])
    def scrape_website():
        if not scraper_available:
            return jsonify({'success': False, 'error': 'Web scraper not available'}), 500
            
        data = request.get_json()
        url = data.get('url')
        format = data.get('format', 'json')  # Default to JSON
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        if not scraper_is_valid_url(url):
            return jsonify({'success': False, 'error': 'Invalid URL format'}), 400
        
        try:
            scraper = WebScraper()
            # Save as JSON or TXT based on format parameter
            save_as_json = (format == 'json')
            result = scraper.scrape(url, save_as_json=save_as_json)
            
            if result['success']:
                return jsonify({
                    'success': True, 
                    'filepath': result['filepath'],
                    'filename': os.path.basename(result['filepath']),
                    'format': format
                })
            else:
                return jsonify({'success': False, 'error': result['error']}), 400
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/scraper/download/<filename>')
    def download_scraped_file(filename):
        try:
            # Security check - only allow files from outputs directory
            safe_filename = os.path.basename(filename)
            file_path = os.path.join('modules', 'scraper', 'outputs', safe_filename)
            
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
            else:
                return jsonify({'success': False, 'error': 'File not found'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # Routes for Video Compressor
    @app.route('/api/compressor/compress', methods=['POST'])
    def compress_video():
        if not compressor_available:
            return jsonify({'success': False, 'error': 'Video compressor not available'}), 500
            
        if 'video' not in request.files:
            return jsonify({'success': False, 'error': 'No video file provided'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        compression_level = request.form.get('compression_level', 'medium')
        target_size = request.form.get('target_size', type=int)
        
        try:
            # Create a temporary directory for processing
            temp_dir = tempfile.mkdtemp()
            filename = secure_filename(file.filename)
            input_path = os.path.join(temp_dir, filename)
            
            # Save uploaded file
            file.save(input_path)
            
            # Process video
            result = video_compressor.process_video(
                input_path, 
                compression_level=compression_level,
                target_size_mb=target_size
            )
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
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
            # Clean up temp directory on error
            if 'temp_dir' in locals():
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/compressor/download/<file_id>')
    def download_compressed_video(file_id):
        try:
            # Find the compressed video file
            for file in os.listdir(os.path.join('modules', 'compressor', 'compressed')):
                if file_id in file:
                    file_path = os.path.join('modules', 'compressor', 'compressed', file)
                    if os.path.exists(file_path):
                        return send_file(file_path, as_attachment=True)
            
            return jsonify({'success': False, 'error': 'Video file not found'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # Routes for Video Downloader
    @app.route('/api/downloader/download', methods=['POST'])
    def download_video():
        if not downloader_available:
            return jsonify({'success': False, 'error': 'Video downloader not available (yt-dlp not installed)'}), 500
            
        data = request.get_json()
        url = data.get('url')
        format_type = data.get('format', 'mp4')
        quality = data.get('quality', 'medium')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        try:
            download_id = str(uuid.uuid4())
            downloads[download_id] = {
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
                'outtmpl': f'{DOWNLOAD_DIR}/{download_id}.%(ext)s',
                'noplaylist': True,
                'quiet': False,
                'progress_hooks': [lambda d: progress_hook(d, download_id)],
                'socket_timeout': 30,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'retries': 5,
            }
            
            # Format/quality settings
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
            else:  # mp4 or other video formats
                if quality == "high":
                    ydl_opts['format'] = 'best[ext=mp4]/best'
                elif quality == "medium":
                    ydl_opts['format'] = 'worst[ext=mp4]/worst'
                else:  # low
                    ydl_opts['format'] = 'worst[ext=mp4]/worst'
            
            # Start download in background thread
            def download_thread():
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        downloads[download_id]["status"] = "completed"
                        downloads[download_id]["title"] = info.get('title', 'Unknown')
                        downloads[download_id]["duration"] = info.get('duration', 0)
                        # Get file size
                        pattern = os.path.join(DOWNLOAD_DIR, f"{download_id}.*")
                        files = glob.glob(pattern)
                        if files:
                            downloads[download_id]["fileSize"] = os.path.getsize(files[0])
                except Exception as e:
                    downloads[download_id]["status"] = "failed"
                    downloads[download_id]["errorMessage"] = str(e)
            
            thread = threading.Thread(target=download_thread)
            thread.start()
            
            return jsonify({
                'success': True,
                'download_id': download_id
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/downloader/downloads', methods=['GET'])
    def get_downloads():
        return jsonify(list(downloads.values()))

    @app.route('/api/downloader/downloads/<download_id>', methods=['DELETE'])
    def delete_download(download_id):
        if download_id in downloads:
            # Delete the file if it exists
            pattern = os.path.join(DOWNLOAD_DIR, f"{download_id}.*")
            files = glob.glob(pattern)
            for file in files:
                try:
                    os.remove(file)
                except:
                    pass
            # Remove from downloads list
            del downloads[download_id]
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Download not found'}), 404

    @app.route('/api/downloader/download/<download_id>')
    def download_file(download_id):
        try:
            # Look for the downloaded file
            pattern = os.path.join(DOWNLOAD_DIR, f"{download_id}.*")
            files = glob.glob(pattern)
            
            if files:
                return send_file(files[0], as_attachment=True)
            else:
                return jsonify({'success': False, 'error': 'File not found'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # Health check route
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'ok',
            'scraper': scraper_available,
            'compressor': compressor_available,
            'downloader': downloader_available
        })

    return app

def open_browser():
    """Open the web browser after a short delay"""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://127.0.0.1:4444')

def main():
    print("=" * 70)
    print("     MULTIFUNCTIONAL APPLICATION")
    print("     Web Scraper | Video Compressor | Video Downloader")
    print("=" * 70)
    
    # Check FFmpeg installation and try to install if needed
    print("\nChecking FFmpeg installation...")
    ffmpeg_report = check_ffmpeg()
    
    if not ffmpeg_report['installed']:
        print("⚠️  FFmpeg is not installed or not accessible")
        print("Trying to install FFmpeg automatically...")
        if install_ffmpeg():
            print("✅ FFmpeg installed successfully")
            ffmpeg_report = check_ffmpeg()  # Recheck
        else:
            print("❌ Failed to install FFmpeg automatically")
            print("Video compression features will be disabled")
    else:
        print("✅ FFmpeg is properly installed")
    
    print("\nStarting unified web server...")
    print("Server will be available at: http://127.0.0.1:4444")
    print("Press Ctrl+C to stop the server\n")
    
    # Start browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # Create and run the app
        app = create_app()
        app.run(debug=True, host='127.0.0.1', port=4444, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:
        print(f"\nError starting server: {str(e)}")

if __name__ == "__main__":
    main()