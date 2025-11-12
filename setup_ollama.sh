#!/usr/bin/env bash
# Arabella Quick Setup Script
# This script installs Ollama models and verifies the installation

set -e  # Exit on error

echo "======================================================================"
echo "Arabella Setup Script"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Ollama is installed
echo "Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}✗ Ollama is not installed${NC}"
    echo "Please install Ollama from https://ollama.ai"
    exit 1
fi
echo -e "${GREEN}✓ Ollama is installed${NC}"
echo ""

# Check if Ollama is running
echo "Checking if Ollama service is running..."
if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Ollama service is not running${NC}"
    echo "Please start Ollama in another terminal:"
    echo "  ollama serve"
    echo ""
    echo "Or this script can try to start it in the background (y/n)?"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Starting Ollama in background..."
        ollama serve > /dev/null 2>&1 &
        sleep 2
        if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Ollama service started${NC}"
        else
            echo -e "${RED}✗ Failed to start Ollama${NC}"
            exit 1
        fi
    else
        echo "Please start Ollama manually and run this script again."
        exit 1
    fi
else
    echo -e "${GREEN}✓ Ollama service is running${NC}"
fi
echo ""

# Pull required models
echo "======================================================================"
echo "Pulling Ollama Models"
echo "======================================================================"
echo "This may take several minutes depending on your connection..."
echo ""

models=("nomic-embed-text:v1.5" "llama3.2:3b")

for model in "${models[@]}"; do
    echo "Pulling ${model}..."
    if ollama pull "$model"; then
        echo -e "${GREEN}✓ ${model} installed${NC}"
    else
        echo -e "${RED}✗ Failed to pull ${model}${NC}"
        exit 1
    fi
    echo ""
done

echo "======================================================================"
echo "Model Installation Complete"
echo "======================================================================"
echo ""

# List installed models
echo "Installed Ollama models:"
ollama list
echo ""

echo "======================================================================"
echo "Running System Verification"
echo "======================================================================"
echo ""

# Run verification script if it exists
if [ -f "verify_installation.py" ]; then
    if command -v uv &> /dev/null; then
        uv run python verify_installation.py
    else
        python verify_installation.py
    fi
else
    echo -e "${YELLOW}⚠ verify_installation.py not found, skipping verification${NC}"
fi

echo ""
echo "======================================================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Initialize databases:    make init"
echo "  2. Run tests:               make test"
echo "  3. Start the application:   make run"
echo "  4. Visit:                   http://localhost:8000/docs"
echo ""
