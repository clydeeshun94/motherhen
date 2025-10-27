# MotherHen - Unified Multifunctional Application

A comprehensive Python application that combines three powerful tools into one unified interface:

- 🕷️ **Web Scraper** - Extract content from websites
- 🎬 **Video Compressor** - Compress videos with different quality levels  
- ⬇️ **Video Downloader** - Download videos from various platforms

## 🏗️ Project Structure

```
motherhen/
├── backend/                    # Backend logic and API
│   ├── modules/               # Core functionality modules
│   │   ├── scraper/          # Web scraping logic
│   │   ├── compressor/       # Video compression logic
│   │   └── downloader/       # Video download logic (integrated)
│   ├── downloads/            # Downloaded videos storage
│   ├── compressed/           # Compressed videos storage
│   ├── main.py              # Unified application entry point
│   └── requirements.txt     # Python dependencies
├── build/                    # Pre-built frontend files
└── start.py                 # Simple startup script
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- FFmpeg (for video compression and audio extraction)

### Installation

1. **Clone/Navigate to the project:**
   ```bash
   cd motherhen
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Start the application:**
   ```bash
   python start.py
   ```

## ☁️ Deployment Options

### Option 1: Full Application Deployment (Recommended)

Deploy the entire application as a single unit where the Python backend serves the pre-built React frontend files.

#### Using Docker (Easiest)
```bash
docker-compose up -d
```

#### Manual Deployment
1. Install Python dependencies and run:
   ```bash
   pip install -r requirements.txt
   python backend/main.py
   ```

### Option 2: Platform-as-a-Service (Railway, Heroku, etc.)

1. Push this repository to your preferred platform
2. The platform will automatically detect and use the Dockerfile or railway.json
3. The backend will serve the pre-built frontend from the build directory

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 📝 Notes

- The application automatically tries to install FFmpeg if not found
- All downloaded and compressed files are stored in respective directories
- The backend serves the pre-built frontend files directly

4. **Open your browser:**
   The application will automatically open at `http://localhost:5000`

## 🔧 Features

### Web Scraper
- Extract content from any website
- Save as JSON or plain text
- Handles various content types
- Respectful scraping with delays

### Video Compressor
- Multiple compression levels (Low, Medium, High)
- Target file size option
- Automatic FFmpeg installation
- Preserves video quality while reducing size

### Video Downloader
- Support for YouTube, TikTok, Instagram, Facebook, and more
- Multiple quality options (480p, 720p, 1080p)
- Audio-only downloads (MP3)
- Progress tracking
- Batch download management

## 🛠️ Technical Details

### Backend Architecture
- Flask web server with REST API
- Modular design - each component is independent
- Unified main.py - single entry point that orchestrates all modules
- Error handling - graceful degradation if modules unavailable

### API Endpoints

#### Web Scraper
- `POST /api/scraper/scrape` - Scrape a website
- `GET /api/scraper/download/<filename>` - Download scraped content

#### Video Compressor
- `POST /api/compressor/compress` - Compress video file
- `GET /api/compressor/download/<file_id>` - Download compressed video

#### Video Downloader
- `POST /api/downloader/download` - Start video download
- `GET /api/downloader/downloads` - List all downloads
- `GET /api/downloader/download/<download_id>` - Download video file
- `DELETE /api/downloader/downloads/<download_id>` - Delete download

### Frontend
- Pure HTML/CSS/JavaScript - no framework dependencies
- Responsive design - works on desktop and mobile
- Real-time updates - progress tracking for downloads
- Tabbed interface - easy switching between tools

## 🔧 Configuration

### Environment Variables
- `MOTHERHEN_PORT` - Server port (default: 5000)
- `MOTHERHEN_HOST` - Server host (default: 127.0.0.1)

### Module Configuration
Each module can be configured independently:
- Scraper settings in `backend/modules/scraper/config/settings.py`
- Compressor presets in `backend/modules/compressor/video_compressor.py`

## 🐛 Troubleshooting

### FFmpeg Issues
If video compression fails:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Module Import Errors
Ensure you're running from the correct directory:
```bash
cd motherhen
python start.py
```

### Port Already in Use
Change the port in backend/main.py or kill the process:
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>
```

## 📝 Development

### Adding New Features
1. Create module in backend/modules/
2. Add routes in backend/main.py
3. Update frontend interface (in build directory)
4. Test integration

### Running in Development Mode
```bash
cd backend
python main.py
```

## 📄 License
This project is open source. Feel free to modify and distribute.

## 🤝 Contributing
1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

MotherHen - One application, three powerful tools. 🐣