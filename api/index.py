"""
Vercel Python entrypoint for Flask (native WSGI)

Expose the Flask WSGI `app` at module scope. Vercel's Python runtime
can invoke WSGI apps directly without additional adapters.
"""

import os
import sys

# Ensure project root is on sys.path so we can import `app.py`
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import app as _flask_app

# Export as `app` to match Vercel's expected symbol
app = _flask_app
