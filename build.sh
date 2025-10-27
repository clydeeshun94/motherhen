#!/bin/bash
echo "Building MotherHen for deployment..."

# Build frontend
echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Build complete!"