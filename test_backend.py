#!/usr/bin/env python3
"""
Quick test script to verify backend functionality
"""

import requests
import json
import time
import threading
import sys
import os

# Add backend path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_backend():
    """Test backend endpoints"""
    base_url = "http://localhost:5002"
    
    print("Testing backend endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Modules: {data['modules']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test web scraper
    try:
        test_data = {
            "url": "https://httpbin.org/html",
            "format": "json"
        }
        response = requests.post(f"{base_url}/api/scraper/scrape", 
                               json=test_data, timeout=10)
        if response.status_code == 200:
            print("✅ Web scraper endpoint working")
        else:
            print(f"❌ Web scraper failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Web scraper error: {e}")

def start_backend():
    """Start backend server"""
    from main import MotherHenApp
    app = MotherHenApp()
    app.run(host='127.0.0.1', port=5002, debug=False)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode - assume server is running
        test_backend()
    else:
        # Start server
        print("Starting MotherHen backend...")
        start_backend()