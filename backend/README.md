# Multifunctional Tool Backend

This is the backend for the Multifunctional Tool application with a modular architecture.

## Architecture

The backend is organized in a modular way where each functionality has its own dedicated module:

```
backend/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── modules/
│   ├── scraper/           # Web scraper module
│   │   ├── scraper.py     # Main scraper logic
│   │   ├── content_parser.py
│   │   ├── file_manager.py
│   │   ├── utils.py
│   │   └── outputs/       # Scraped content output
│   ├── compressor/        # Video compressor module
│   │   ├── video_compressor.py
│   │   ├── ffmpeg_checker.py
│   │   ├── ffmpeg_installer.py
│   │   └── compressed/    # Compressed videos output
│   └── downloader/        # Video downloader module
│       └── (yt-dlp based functionality)
└── downloads/             # Downloaded videos directory
```

## Modules

### Scraper Module
Handles web scraping functionality:
- Extract content from websites
- Save as text or JSON format
- Respectful scraping with rate limiting

### Compressor Module
Handles video compression functionality:
- Compress videos to reduce file size
- Multiple compression levels
- Automatic FFmpeg installation

### Downloader Module
Handles video downloading functionality:
- Download videos from various platforms
- Multiple format options (MP4, MP3)
- Quality selection

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

This will start the server on http://localhost:4444 and automatically open your browser.

## API Endpoints

### Web Scraper
- `POST /api/scraper/scrape` - Scrape a website
- `GET /api/scraper/download/<filename>` - Download scraped content

### Video Compressor
- `POST /api/compressor/compress` - Compress a video
- `GET /api/compressor/download/<file_id>` - Download compressed video

### Video Downloader
- `POST /api/downloader/download` - Download a video from a URL
- `GET /api/downloader/downloads` - Get list of downloads
- `DELETE /api/downloader/downloads/<id>` - Delete a download
- `GET /api/downloader/download/<id>` - Download the video file

## Extensibility

To add a new module:

1. Create a new folder in the `modules` directory
2. Implement the functionality in Python files within that folder
3. Add routes in `app.py` to expose the functionality via API
4. The new module will be automatically integrated into the system

This modular approach makes it easy to extend the application with new features.