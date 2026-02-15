#!/bin/bash

# Setup script for lec_final virtual environment
# Usage: ./setup_venv.sh

set -e  # Exit on error

echo "=========================================="
echo "Setting up lec_final virtual environment"
echo "=========================================="

# Check Python version
echo ""
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "Virtual environment already exists. Removing old one..."
    rm -rf .venv
fi
python3 -m venv .venv

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing requirements..."
pip install -r requirements.txt

# Verify installation
echo ""
echo "=========================================="
echo "Verifying installation..."
echo "=========================================="

echo ""
echo "Python packages installed:"
pip list | grep -E "airflow|boto3|pyspark|psycopg2|pandas|pyarrow"

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
echo ""

