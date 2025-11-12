# Arabella Setup Guide

Complete setup instructions for the Arabella Graph-RAG system.

## Prerequisites

- Python 3.13+
- [Ollama](https://ollama.ai) (for embeddings and language models)
- [uv](https://github.com/astral-sh/uv) (Python package manager)

## Step-by-Step Setup

### 1. Install Ollama

Download and install Ollama from https://ollama.ai

Verify installation:
```bash
ollama --version
```

### 2. Start Ollama Service

In a separate terminal, start the Ollama service:
```bash
ollama serve
```

Keep this running in the background.

### 3. Install Python Dependencies

```bash
make install
```

This will:
- Install all Python packages using `uv`
- Download required NLTK data (stopwords, punkt)

### 4. Install Ollama Models

Pull the required models (this may take several minutes):
```bash
make setup-ollama
```

This downloads:
- `nomic-embed-text:v1.5` - For generating embeddings (768 dimensions)
- `llama3.2:3b` - For language generation

You can also pull models manually:
```bash
ollama pull nomic-embed-text:v1.5
ollama pull llama3.2:3b
```

### 5. Verify Installation

Run the verification script:
```bash
make verify
```

This checks:
- ✓ Python version (3.13+)
- ✓ All dependencies installed
- ✓ NLTK data downloaded
- ✓ Project structure
- ✓ Custom modules can be imported
- ✓ Ollama is accessible
- ✓ Required models are available

### 6. Initialize Databases

```bash
make init
```

This initializes:
- KuzuDB (graph database)
- Qdrant (vector database)

### 7. Run Tests

```bash
make test
```

To run specific test categories:
```bash
make test-unit        # Unit tests only
make test-integration # Integration tests only
make test-coverage    # With coverage report
```

### 8. Start the Application

```bash
make run
```

The API will be available at:
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **API Endpoint**: http://localhost:8000

## Common Issues & Solutions

### Issue: "model not found" error

**Solution**: Make sure models are pulled
```bash
make setup-ollama
```

### Issue: Ollama connection failed

**Solution**: Ensure Ollama is running
```bash
# In a separate terminal
ollama serve
```

### Issue: SSL Certificate errors with NLTK

**Solution**: The Makefile handles this automatically, but if needed:
```bash
uv run python -c "import ssl; import nltk; ssl._create_default_https_context = ssl._create_unverified_context; nltk.download('stopwords'); nltk.download('punkt')"
```

### Issue: Tests failing with "fixture not found"

**Solution**: Make sure you're using pytest from the uv environment:
```bash
make test  # Uses uv run pytest
```

### Issue: Database path errors

**Solution**: Clean and reinitialize
```bash
make clean
make init
```

## Project Structure

```
Arabella/
├── crawler/          # Web crawler for gathering data
├── db/              # Database wrappers (KuzuDB, QdrantDB)
├── query_bridge/    # Query transformation
├── rag/             # Graph-RAG implementation
├── scripts/         # Utility scripts
├── tests/           # Test suite
├── main.py          # FastAPI application
├── Makefile         # Development commands
└── verify_installation.py  # System verification
```

## Development Workflow

1. **Make changes** to the code
2. **Run tests** to verify: `make test`
3. **Verify installation** if adding dependencies: `make verify`
4. **Clean temporary files**: `make clean`
5. **Backup databases** before major changes: `make backup-db`

## Environment Variables

You can customize behavior with these environment variables:

```bash
# Ollama host (default: http://127.0.0.1:11434)
export OLLAMA_HOST=http://localhost:11434

# Database paths (default: ./kuzu_db and ./vector_db)
export KUZU_DB_PATH=./kuzu_db
export QDRANT_PATH=./vector_db
```

## Docker Deployment (Optional)

Build and run with Docker:
```bash
make docker-up
```

Stop Docker services:
```bash
make docker-down
```

View logs:
```bash
make docker-logs
```

## Next Steps

After setup is complete:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Run examples**: Check `tests/` for usage examples
3. **Read documentation**: See README.md for architecture details
4. **Start crawling**: Use the crawler module to gather data
5. **Build RAG pipeline**: Index documents and query them

## Getting Help

- Check verification output: `make verify`
- Review test failures: `make test -v`
- Consult the README.md for architecture details
- Check Ollama logs if embedding issues persist

## Quick Reference

```bash
# Essential commands
make install        # Install dependencies
make setup-ollama   # Pull Ollama models
make verify         # Verify installation
make init          # Initialize databases
make test          # Run tests
make run           # Start application

# Maintenance
make clean         # Clean temporary files
make backup-db     # Backup databases

# Docker
make docker-up     # Start with Docker
make docker-down   # Stop Docker
make docker-logs   # View logs
```
