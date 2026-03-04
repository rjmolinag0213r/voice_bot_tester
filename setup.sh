#!/bin/bash

# Voice Bot Testing System - Setup Script
# This script sets up the environment for the voice bot testing system

set -e

echo "========================================"
echo "Voice Bot Testing System Setup"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

if ! python3 -c 'import sys; assert sys.version_info >= (3, 8)' 2>/dev/null; then
    echo "ERROR: Python 3.8 or higher is required"
    exit 1
fi

# Create virtual environment (optional)
if [ ! -d "venv" ]; then
    echo ""
    read -p "Create virtual environment? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        echo "Virtual environment created. Activate it with: source venv/bin/activate"
    fi
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo "Dependencies installed successfully!"

# Check for .env file
echo ""
if [ ! -f ".env" ]; then
    echo "No .env file found. Creating from template..."
    cp .env.example .env
    echo ".env file created. Please edit it with your API credentials."
    echo ""
    echo "Required credentials:"
    echo "  - TWILIO_ACCOUNT_SID"
    echo "  - TWILIO_AUTH_TOKEN"
    echo "  - TWILIO_PHONE_NUMBER"
    echo "  - OPENROUTER_API_KEY"
else
    echo ".env file already exists."
fi

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p recordings reports logs
echo "Directories created."

# Final message
echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API credentials"
echo "2. Run 'python main.py list-personas' to see available test personas"
echo "3. Run 'python main.py run' to execute the test suite"
echo ""
echo "For more information, see README.md"
echo ""
