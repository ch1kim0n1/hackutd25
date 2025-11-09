#!/usr/bin/env python3
"""
Simple test script to start the APEX backend server
"""

import os
import sys

# Change to backend directory
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
os.chdir(backend_dir)

# Add backend to path
sys.path.insert(0, backend_dir)

try:
    print("Importing FastAPI app...")
    from app.main import app
    print("App imported successfully")

    print("Importing uvicorn...")
    import uvicorn
    print("Uvicorn imported successfully")

    print("Starting server on http://127.0.0.1:8000")
    print("API Docs will be at: http://127.0.0.1:8000/docs")
    print("Health check at: http://127.0.0.1:8000/health")
    print("")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
