#!/bin/bash
# JMeter Toolkit Development Server Starter

echo "🚀 Starting JMeter Toolkit Development Server with UV"
echo ""

# Set environment to use official PyPI to avoid mirror issues
export UV_INDEX_URL=https://pypi.org/simple

# Start the server
uv run python dev_server.py
