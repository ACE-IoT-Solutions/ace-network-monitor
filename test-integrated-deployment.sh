#!/bin/bash
# Test script for integrated deployment (API + built frontend)
# This simulates how the Docker container runs

set -e

echo "🔨 Building Vue.js frontend..."
cd frontend
npm run build
cd ..

echo ""
echo "✅ Frontend built successfully!"
echo ""
echo "🚀 Starting integrated server (API + Frontend)..."
echo ""
echo "   Dashboard: http://localhost:8506"
echo "   API Docs:  http://localhost:8506/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the monitor with API server
uv run python main.py monitor
