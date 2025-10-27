# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including ffmpeg and Node.js (for serving build files if needed)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ffmpeg \
    && curl -sL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy backend files
COPY backend/ ./backend

# Copy frontend build files (these will be served by Flask)
COPY build/ ./build

# Copy startup script
COPY start.py ./start.py

# Install Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose port (Railway will map this automatically)
EXPOSE 5000

# Default command to run the application
CMD ["python", "start.py"]
