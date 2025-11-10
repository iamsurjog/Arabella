.PHONY: help install test run docker-up docker-down clean init setup-ollama verify

help:
	@echo "Arabella - Development Commands"
	@echo "================================"
	@echo "make install      - Install dependencies"
	@echo "make setup-ollama - Pull required Ollama models"
	@echo "make verify       - Verify installation"
	@echo "make init         - Initialize databases"
	@echo "make test         - Run all tests"
	@echo "make test-unit    - Run unit tests only"
	@echo "make test-integration - Run integration tests"
	@echo "make test-e2e     - Run end-to-end tests"
	@echo "make test-coverage - Run tests with coverage"
	@echo "make run          - Run development server"
	@echo "make docker-up    - Start Docker services"
	@echo "make docker-down  - Stop Docker services"
	@echo "make clean        - Clean temporary files"

install:
	uv sync
	uv run python -c "import ssl; import nltk; ssl._create_default_https_context = ssl._create_unverified_context; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"

setup-ollama:
	@echo "Setting up Ollama models..."
	@./setup_ollama.sh

verify:
	uv run python verify_installation.py

init:
	uv run python scripts/init_databases.py

test:
	uv run pytest -v

test-unit:
	uv run pytest -v -m unit

test-integration:
	uv run pytest -v -m integration

test-e2e:
	uv run pytest -v -m e2e -s

test-coverage:
	uv run pytest --cov=. --cov-report=html --cov-report=term

run:
	uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -f .coverage

backup-db:
	mkdir -p backups
	cp -r kuzu_db backups/kuzu_db_$$(date +%Y%m%d_%H%M%S)
	cp -r vector_db backups/vector_db_$$(date +%Y%m%d_%H%M%S)
	@echo "Databases backed up to backups/"
