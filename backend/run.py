import os
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
sys.path[:0] = [BACKEND_DIR, PROJECT_DIR]

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
