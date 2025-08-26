#!/usr/bin/env python3
"""
Debug runner for the Flask application
"""
import os
import sys
from main import app

if __name__ == '__main__':
    print("=== DEBUG MODE ===")
    print("Starting Flask app in debug mode...")
    print("Available endpoints:")
    print("  GET  /")
    print("  GET  /health")
    print("  GET  /test")
    print("  POST /generate-presentation")
    print()
    
    # Set debug environment
    os.environ['FLASK_DEBUG'] = 'True'
    
    port = int(os.environ.get('PORT', 5000))
    print(f"Server will run on: http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    print("=" * 40)
    
    app.run(
        host='127.0.0.1',  # Use localhost for debugging
        port=port,
        debug=True,
        use_reloader=True
    )
