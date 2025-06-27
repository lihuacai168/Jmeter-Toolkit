#!/bin/bash
# JMeter Toolkit Development Setup Script

set -e

echo "🚀 Setting up JMeter Toolkit development environment..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "📍 Using Python $python_version"

if [[ $(python3 -c "import sys; print(1 if sys.version_info < (3, 9) else 0)") -eq 1 ]]; then
    echo "❌ Python 3.9+ is required. Current version: $python_version"
    exit 1
fi

# Initialize uv project if needed
echo "📦 Initializing uv environment..."
uv venv --python 3.11

# Install development dependencies
echo "📚 Installing development dependencies..."
uv pip install -e ".[dev,test]"

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg

# Create required directories
echo "📁 Creating required directories..."
mkdir -p jmx_files jtl_files reports static templates

# Run initial code formatting
echo "🎨 Running initial code formatting..."
uv run black . --line-length 127
uv run isort . --profile black --line-length 127

# Run tests to verify setup
echo "🧪 Running tests to verify setup..."
uv run pytest tests/ -v

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Quick commands:"
echo "  uv run python main.py    # Start development server"
echo "  uv run pytest           # Run tests"
echo "  uv run black .          # Format code"
echo "  uv run isort .          # Sort imports"
echo "  uv run flake8 .         # Lint code"
echo ""
echo "🎉 You're ready to start developing!"
echo ""
echo "💡 Tips:"
echo "  - Pre-commit hooks will run automatically on commit"
echo "  - Use 'uv run black .' before committing to fix formatting issues"
echo "  - All commands can be run with 'uv run <command>'"
echo ""
echo "To activate the virtual environment manually:"
echo "  source .venv/bin/activate"
