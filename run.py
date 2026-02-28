#!/usr/bin/env python3
"""
Startup script for PLC Instrument Simulator
"""
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path.parent))

if __name__ == "__main__":
    import uvicorn
    from backend.main import app

    print("=" * 60)
    print("PLC Instrument Simulator")
    print("=" * 60)
    print(f"Config: config/instruments.yaml")
    print(f"Web UI: http://0.0.0.0:8000")
    print(f"API Docs: http://0.0.0.0:8000/docs")
    print("=" * 60)
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )
