"""
api/index.py  —  Vercel serverless entry point

Vercel looks for a variable named `app` in this file.
We import FastAPI app from our backend and re-export it here.
All /api/* routes are forwarded here by vercel.json.
"""
import sys
import os

# Make sure the project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.main import app  # noqa: F401 — Vercel needs this name
