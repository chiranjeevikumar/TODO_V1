"""
api/index.py  —  Vercel serverless entry point

Vercel looks for a variable named `app` or `handler` in this file.
We simply import the FastAPI app from our backend package.
All routes (/api/*) will be forwarded here by vercel.json.
"""
import sys
import os

# Make sure the project root is on the Python path
# so `from backend.xxx import yyy` works inside the serverless function
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.main import app  # noqa: F401 — Vercel needs this name
