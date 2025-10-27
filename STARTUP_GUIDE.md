# MotherHen Startup Guide

## Quick Start Options

### 1. Production Mode (Recommended)
```bash
python3 start_unified.py
```
- Builds frontend automatically if needed
- Serves everything from one server (port 5002)
- Opens browser automatically
- Best for normal usage

### 2. Development Mode
```bash
python3 start_dev.py
```
- Runs backend on port 5002
- Runs frontend dev server on port 3000
- Hot reload for frontend changes
- Best for development

### 3. Original Method
```bash
python3 start.py
```
- Uses the original startup script
- Runs backend only (port 5002)

## Troubleshooting

### "Reddish Orange Screens" Issue
This usually means the frontend is loading but can't connect to the backend. Try:

1. **Use Production Mode**: `python3 start_unified.py`
2. **Check ports**: Make sure backend is on 5002, frontend proxy points to 5002
3. **Rebuild frontend**: Delete `frontend/build` folder and restart

### Testing Backend
```bash
python3 test_backend.py test
```
This tests if the backend endpoints are working (run while server is running).

### Manual Steps
1. **Build frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Start backend**:
   ```bash
   cd backend
   python3 main.py
   ```

## Features Available

### 🌐 Web Scraper
- Paste any website URL
- Choose JSON or TXT format
- Download scraped content

### 🎥 Video Compressor  
- Upload video files
- Choose compression level (low/medium/high)
- Set target file size (optional)
- Download compressed video

### 📱 Video Downloader
- Paste social media video URLs (YouTube, TikTok, etc.)
- Choose format (MP4 video or MP3 audio)
- Choose quality (high/medium/low)
- Track download progress
- Download completed files

## URLs
- **Production**: http://localhost:5002
- **Development Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5002/api/
- **Health Check**: http://localhost:5002/health