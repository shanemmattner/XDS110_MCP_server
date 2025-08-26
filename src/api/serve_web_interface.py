#!/usr/bin/env python3
"""
Simple HTTP server to serve the API web interface
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8053
DIRECTORY = Path(__file__).parent

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        super().end_headers()

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("API Web Interface Server")
    print(f"{'='*60}")
    print(f"Serving directory: {DIRECTORY}")
    print(f"Web interface will be available at: http://localhost:{PORT}/api_web_interface.html")
    print("\nMake sure the API is also running:")
    print("  python3 src/api/flexible_variable_api.py")
    print(f"{'='*60}\n")
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()