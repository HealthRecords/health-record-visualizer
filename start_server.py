#!/usr/bin/env python3
"""
Health Data Explorer Server Startup Script
==========================================

This script provides an easy way to start the Health Data Explorer web server.
It handles configuration validation and provides helpful error messages.
"""

import sys
import os
from pathlib import Path
import argparse

def check_requirements():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import jinja2
        import pydantic
        print("✓ All required dependencies found")
        return True
    except ImportError as e:
        print(f"✗ Missing required dependency: {e.name}")
        print("Please install requirements with: python -m pip install -r requirements.txt")
        return False

def check_config(data_dir=None):
    """Check if config.py exists and is valid"""
    if data_dir:
        # Override config with command line data directory
        data_path = Path(data_dir)
        if data_path.exists():
            print(f"✓ Using data directory: {data_path}")
            # Set environment variable for FastAPI app to read
            import os
            os.environ['HEALTH_DATA_DIR'] = str(data_path.absolute())
            # Also update config in this process
            import config
            config.set_source_dir(data_path)
            return True
        else:
            print(f"✗ Data directory not found: {data_path}")
            return False
    else:
        # Use existing config.py
        try:
            import config
            if hasattr(config, 'get_source_dir'):
                source_dir = config.get_source_dir()
                if source_dir.exists():
                    print(f"✓ Data directory found: {source_dir}")
                    return True
                else:
                    print(f"✗ Data directory not found: {source_dir}")
                    print("Please ensure your Apple Health export data is in the correct location.")
                    return False
            else:
                print("✗ config.py missing 'get_source_dir' function")
                return False
        except ImportError:
            print("✗ config.py not found")
            print("Please create config.py with your data directory path")
            return False

def main():
    parser = argparse.ArgumentParser(description="Start Health Data Explorer web server")
    parser.add_argument("--data-dir", help="Path to health data directory (overrides config.py)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--no-checks", action="store_true", help="Skip configuration checks")
    args = parser.parse_args()

    print("Health Data Explorer - Starting Server")
    print("=" * 40)

    if not args.no_checks:
        if not check_requirements():
            sys.exit(1)
        
        if not check_config(args.data_dir):
            sys.exit(1)
        
        print()

    print(f"Starting server at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()