# Vercel Serverless entrypoint for Flask via vercel-wsgi
# This adapts the Flask WSGI app defined in app.py to Vercel's serverless runtime

from vercel_wsgi import handle
from app import app

# Vercel expects a function named `handler`
# It will receive (request, context) and we delegate to vercel-wsgi

def handler(request, context):
    return handle(app, request, context)
