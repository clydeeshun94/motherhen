from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import uuid
from datetime import datetime
import threading
import glob

app = Flask(__name__)
CORS(app)

downloads = {}
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


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


def build_ydl_opts(download_id, url, format_type, quality):
    """Build yt_dlp options dynamically for any platform"""
    base_opts = {
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
        ydl_opts = {
            **base_opts,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality_map.get(quality, "192"),
            }],
        }
    else:
        quality_map = {"low": "480", "medium": "720", "high": "1080"}
        target_height = quality_map.get(quality, "720")
        ydl_opts = {
            **base_opts,
            'format': (
                f'bestvideo[height<={target_height}]+bestaudio/best'
                f'/best[height<={target_height}]/best'
            ),
            'merge_output_format': 'mp4',
        }

    # TikTok watermark removal (yt-dlp handles automatically)
    if "tiktok.com" in url:
        ydl_opts['format'] = 'best[format_id*=nowm]/best'  # prefer “no watermark” versions

    # Instagram/Facebook special headers
    if any(x in url for x in ["instagram.com", "facebook.com"]):
        ydl_opts['http_headers'] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept-Language': 'en-US,en;q=0.9'
        }

    return ydl_opts


def download_video(download_id, url, format_type, quality):
    try:
        downloads[download_id]["status"] = "downloading"
        downloads[download_id]["progress"] = 0

        ydl_opts = build_ydl_opts(download_id, url, format_type, quality)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Find the downloaded file
            pattern = f'{DOWNLOAD_DIR}/{download_id}.*'
            files = glob.glob(pattern)
            if not files:
                raise Exception("Downloaded file not found")

            file_path = files[0]
            file_size = os.path.getsize(file_path)
            file_ext = os.path.splitext(file_path)[1]

            downloads[download_id].update({
                "status": "completed",
                "progress": 100,
                "title": info.get("title", "Unknown"),
                "duration": info.get("duration", 0),
                "fileSize": file_size,
                "fileExtension": file_ext,
                "downloadUrl": f"/download/{download_id}"
            })

    except Exception as e:
        print(f"Download error for {download_id}: {str(e)}")
        downloads[download_id].update({
            "status": "failed",
            "errorMessage": str(e)
        })


@app.route('/api/downloads', methods=['POST'])
def create_download():
    try:
        data = request.json
        url = data.get("url")
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        download_id = str(uuid.uuid4())
        downloads[download_id] = {
            "_id": download_id,
            "url": url,
            "format": data.get("format", "mp4"),
            "quality": data.get("quality", "medium"),
            "status": "pending",
            "progress": 0,
            "createdAt": datetime.now().isoformat()
        }

        thread = threading.Thread(
            target=download_video,
            args=(download_id, url, data.get("format", "mp4"), data.get("quality", "medium"))
        )
        thread.daemon = True
        thread.start()

        return jsonify(downloads[download_id])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/downloads', methods=['GET'])
def get_downloads():
    return jsonify(list(downloads.values()))


@app.route('/api/downloads/<download_id>', methods=['DELETE'])
def delete_download(download_id):
    if download_id in downloads:
        try:
            pattern = f'{DOWNLOAD_DIR}/{download_id}.*'
            files = glob.glob(pattern)
            for file in files:
                os.remove(file)
        except:
            pass
        del downloads[download_id]
        return jsonify({'success': True})
    return jsonify({'error': 'Download not found'}), 404

@app.route('/api/downloads/<download_id>', methods=['DELETE'])
def delete_download(download_id):
    if download_id not in downloads:
        return jsonify({'error': 'Download not found'}), 404
    
    # Delete the file if it exists
    pattern = f'{DOWNLOAD_DIR}/{download_id}.*'
    files = glob.glob(pattern)
    for file_path in files:
        try:
            os.remove(file_path)
        except OSError:
            pass
    
    # Remove from downloads dict
    del downloads[download_id]
    return jsonify({'message': 'Download deleted'})


@app.route('/download/<download_id>')
def download_file(download_id):
    if download_id not in downloads:
        return "Download not found", 404

    download = downloads[download_id]
    if download.get('status') != 'completed':
        return "Download not completed", 400

    pattern = f'{DOWNLOAD_DIR}/{download_id}.*'
    files = glob.glob(pattern)
    if not files:
        return "File not found", 404

    file_path = files[0]
    title = "".join(c for c in download.get('title', 'download') if c.isalnum() or c in (' ', '-', '_')).strip()
    ext = os.path.splitext(file_path)[1].replace('.', '')
    filename = f"{title}.{ext}"

    mimetype = 'audio/mpeg' if ext.lower() == 'mp3' else 'video/mp4'

    return send_file(file_path, as_attachment=True, download_name=filename, mimetype=mimetype)


if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
