#!/bin/bash
set -e

echo "=================================="
echo "🔍 V7.5 DOWNLOAD SERVICE START"
echo "=================================="

# Use PORT environment variable from Railway, or default to 8010
PORT=${PORT:-8010}

echo "PORT environment variable: '${PORT}'"
echo "Using port: $PORT"

echo "=================================="
echo "🚀 Starting download service..."
echo "=================================="

# Start the Python application
exec python3 main.py
