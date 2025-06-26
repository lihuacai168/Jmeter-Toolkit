#!/usr/bin/env python3
"""Development server runner."""
import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Run development server."""
    try:
        # Import after path setup
        import uvicorn
        from config import settings
        
        print(f"Starting {settings.app_name} v{settings.app_version}")
        print(f"Server will run at: http://{settings.host}:{settings.port}")
        print("API Documentation: http://localhost:8000/docs")
        print("Press Ctrl+C to stop the server")
        
        # Set development environment
        os.environ.setdefault("DEBUG", "true")
        os.environ.setdefault("RELOAD", "true")
        
        # Run server
        uvicorn.run(
            "main_dev:app",
            host=settings.host,
            port=settings.port,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()