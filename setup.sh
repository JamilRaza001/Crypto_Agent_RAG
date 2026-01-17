#!/bin/bash
# Quick setup script for the Crypto Agent project

echo "=== Crypto Agent Setup ==="
echo ""

# Check Python version
echo "Checking Python version..."
python --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment (instructions)
echo ""
echo "Virtual environment created!"
echo "To activate:"
echo "  Windows: venv\\Scripts\\activate"
echo "  Linux/Mac: source venv/bin/activate"
echo ""

# Install dependencies (after activation)
echo "After activation, run:"
echo "  pip install --upgrade pip"
echo "  pip install -r requirements.txt"
echo "  python -m spacy download en_core_web_sm"
echo ""

# Environment setup
echo "Then configure your .env file:"
echo "  cp .env.example .env"
echo "  # Edit .env and add your GEMINI_API_KEY"
echo ""

echo "Get your Gemini API key at: https://aistudio.google.com/app/apikey"
echo ""

echo "Setup instructions complete!"
echo "Next steps: Implement remaining phases (3-8)"
