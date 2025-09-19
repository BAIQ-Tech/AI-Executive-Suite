#!/bin/bash

# AI Executive Suite Startup Script

echo "🚀 Starting AI Executive Suite..."
echo "=================================="

# Set environment variables for development
export FLASK_ENV=development
export DEBUG=true
export FLASK_APP=app.py

# Create necessary directories
mkdir -p uploads
mkdir -p chroma_db
mkdir -p logs

echo "📁 Created necessary directories"

# Check Python version
python_version=$(python --version 2>&1)
echo "🐍 Python version: $python_version"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected"
    echo "   Consider running: source .venv/bin/activate"
fi

# Install/check dependencies
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

echo ""
echo "🌟 AI Executive Suite Features:"
echo "   📄 Document Processing (PDF, Word, Excel, Text, CSV)"
echo "   🔍 Vector-based Semantic Search"
echo "   🧠 AI-powered Document Analysis"
echo "   🔒 Security Scanning and Validation"
echo ""

echo "🌐 Starting web server..."
echo "   Main Interface: http://localhost:5000"
echo "   Upload Page: http://localhost:5000/upload"
echo "   Health Check: http://localhost:5000/health"
echo "   API Documentation: http://localhost:5000/api/documents/"
echo ""

echo "💡 Tips:"
echo "   - Set OPENAI_API_KEY for full AI features"
echo "   - Use Ctrl+C to stop the server"
echo "   - Check logs/ directory for detailed logs"
echo ""

# Start the application
python app.py