#!/bin/bash

# JMeter Toolkit Development Server Starter

echo "🚀 Starting JMeter Toolkit Development Server"
echo ""

# Set development environment variables
export ENVIRONMENT=development
export DEBUG=true
export DATABASE_URL=sqlite:///./jmeter_toolkit_dev.db
export LOG_LEVEL=INFO

# Start the server
python main.py
