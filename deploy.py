#!/usr/bin/env python3
"""
Deployment script for MotherHen application.
This script starts the backend server with pre-built frontend.
"""

import os
import subprocess
import sys
import shutil

def check_build_exists():
    """Check if the frontend build exists"""
    print("Checking for pre-built frontend...")
    build_dir = os.path.join(os.path.dirname(__file__), 'build')
    if not os.path.exists(build_dir):
        print("Error: Pre-built frontend (build directory) not found.")
        return False
    
    index_html = os.path.join(build_dir, 'index.html')
    if not os.path.exists(index_html):
        print("Error: build/index.html not found.")
        return False
    
    print("Pre-built frontend found!")
    return True

def start_backend():
    """Start the Python backend"""
    print("Starting Python backend...")
    backend_script = os.path.join(os.path.dirname(__file__), 'backend', 'main.py')
    
    if not os.path.exists(backend_script):
        print("Error: Backend script not found.")
        return False
    
    try:
        subprocess.run(['python', backend_script], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error starting backend: {e}")
        return False
    except KeyboardInterrupt:
        print("\nShutting down...")
        return True

def main():
    """Main deployment function"""
    print("MotherHen Deployment Script")
    print("=" * 30)
    
    # Check if build exists
    if not check_build_exists():
        print("Cannot start application without pre-built frontend. Exiting.")
        sys.exit(1)
    
    # Start backend
    if not start_backend():
        print("Failed to start backend.")
        sys.exit(1)

if __name__ == "__main__":
    main()