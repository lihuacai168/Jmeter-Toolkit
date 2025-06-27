#!/bin/bash
# 启动被测试服务器

echo "🎯 Starting JMeter Test Server..."
echo ""
echo "📍 Server will run on: http://localhost:3000"
echo "📖 API Documentation: http://localhost:3000/docs"
echo "⏹️  Press Ctrl+C to stop server"
echo ""

# 设置环境变量
export PYTHONUNBUFFERED=1

# 启动服务器
python test_server.py
