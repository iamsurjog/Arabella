#!/bin/bash
# Arabella Setup Script

set -e

echo "================================"
echo "Arabella Setup Script"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if ! command -v python3.13 &> /dev/null; then
    echo -e "${RED}Error: Python 3.13 is required but not found${NC}"
    echo "Please install Python 3.13 first"
    exit 1
fi
echo -e "${GREEN}✓ Python 3.13 found${NC}"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3.13 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Download NLTK data
echo ""
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('stopwords', quiet=True); nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)"
echo -e "${GREEN}✓ NLTK data downloaded${NC}"

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p kuzu_db vector_db backups
echo -e "${GREEN}✓ Directories created${NC}"

# Check if Ollama is installed
echo ""
echo "Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama found${NC}"
    
    echo ""
    echo "Pulling required Ollama models..."
    echo "This may take a while..."
    
    if ollama list | grep -q "nomic-embed-text:v1.5"; then
        echo -e "${YELLOW}nomic-embed-text:v1.5 already pulled${NC}"
    else
        ollama pull nomic-embed-text:v1.5
        echo -e "${GREEN}✓ nomic-embed-text:v1.5 pulled${NC}"
    fi
    
    if ollama list | grep -q "llama3.2:3b"; then
        echo -e "${YELLOW}llama3.2:3b already pulled${NC}"
    else
        ollama pull llama3.2:3b
        echo -e "${GREEN}✓ llama3.2:3b pulled${NC}"
    fi
else
    echo -e "${YELLOW}Warning: Ollama not found${NC}"
    echo "Please install Ollama from https://ollama.ai"
    echo "Then run: ollama pull nomic-embed-text:v1.5 && ollama pull llama3.2:3b"
fi

# Initialize databases
echo ""
echo "Initializing databases..."
python scripts/init_databases.py || echo -e "${YELLOW}Note: Database initialization requires Ollama to be running${NC}"

# Create .env file if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}Please review and update .env file with your configuration${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source .venv/bin/activate"
echo "2. Ensure Ollama is running: ollama serve"
echo "3. Start the application: make run"
echo "   or: uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "For Docker deployment:"
echo "  docker-compose up --build"
echo ""
echo "Run tests:"
echo "  make test"
echo ""
echo "API Documentation will be available at:"
echo "  http://localhost:8000/docs"
echo ""
