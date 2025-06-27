#!/bin/bash
# JMeter Toolkit Development Setup Script

set -e

echo "🚀 Setting up JMeter Toolkit development environment..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "📍 Using Python $python_version"

if [[ $(echo "$python_version < 3.9" | bc -l) -eq 1 ]]; then
    echo "❌ Python 3.9+ is required. Current version: $python_version"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install development dependencies
echo "📚 Installing development dependencies..."
pip install --upgrade pip
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

# Create required directories
echo "📁 Creating required directories..."
mkdir -p jmx_files jtl_files reports static templates

# Run initial code formatting
echo "🎨 Running initial code formatting..."
black . --line-length 127
isort . --profile black --line-length 127

# Run tests to verify setup
echo "🧪 Running tests to verify setup..."
python -m pytest tests/ -v

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Quick commands:"
echo "  make help          # Show all available commands"
echo "  make format        # Format code with black and isort"
echo "  make test          # Run tests"
echo "  make lint          # Run code quality checks"
echo "  make docker-ci     # Test Docker build"
echo ""
echo "🎉 You're ready to start developing!"
echo ""
echo "💡 Tips:"
echo "  - Pre-commit hooks will run automatically on commit"
echo "  - Use 'make format' before committing to fix formatting issues"
echo "  - Run 'make ci-local' to simulate full CI pipeline"
echo ""
echo "To activate the virtual environment manually:"
echo "  source venv/bin/activate"
