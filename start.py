#!/usr/bin/env python3
"""
Production startup script for Railway deployment
Uses gunicorn for production or Flask dev server for local development
"""

import os
import sys

def main():
    # Check if we're on Railway (production)
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        # Production: Use gunicorn
        import subprocess
        port = os.environ.get('PORT', '5000')
        
        # Change to backend directory
        os.chdir('backend')
        
        # Start gunicorn
        cmd = [
            'gunicorn',
            '--bind', f'0.0.0.0:{port}',
            '--workers', '2',
            '--timeout', '120',
            '--keep-alive', '2',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            'main:create_app()',
        ]
        
        print("🚀 Starting MotherHen with Gunicorn (Production)")
        print(f"📍 Binding to 0.0.0.0:{port}")
        
        subprocess.run(cmd)
    else:
        # Development: Use Flask dev server
        sys.path.append('backend')
        from main import main as dev_main
        dev_main()

def create_app():
    """Factory function for gunicorn"""
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    from main import MotherHenApp
    app_instance = MotherHenApp()
    return app_instance.app

if __name__ == "__main__":
    main()