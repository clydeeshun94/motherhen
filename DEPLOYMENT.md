# Deployment Guide

This document explains the different ways to deploy the MotherHen application.

## Option 1: Full Application Deployment (Recommended)

The recommended approach is to deploy the entire application as a single unit, where the Python backend serves the React frontend build files.

### Using Docker (Easiest)

1. Build and run with Docker:
```bash
docker-compose up -d
```

2. Access the application at `http://localhost:5000`

### Manual Deployment

1. Build the React frontend:
```bash
cd frontend
npm install
npm run build
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python backend/main.py
```

## Option 2: Separate Frontend and Backend

### Frontend on Netlify

1. Deploy the frontend folder to Netlify
2. Update the `netlify.toml` file to point to your backend URL
3. Make sure your backend is deployed and accessible

### Backend Deployment Options

1. **Heroku/Render**:
   - Push only the backend code
   - Make sure to build the frontend separately and update API URLs

2. **Traditional Server**:
   - Install Python dependencies
   - Run the Flask application with a WSGI server like Gunicorn

## Environment Variables

The application may require the following environment variables:
- `FLASK_ENV`: Set to "production" for production deployments
- API keys for specific services (if needed)

## Notes

- The backend is configured to serve the frontend build files from `../frontend/build`
- Make sure the build directory exists when running the backend
- For production deployments, consider using a reverse proxy like Nginx