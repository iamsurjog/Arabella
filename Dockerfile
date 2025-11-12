FROM python:3.13-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y git build-essential && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt /app/
COPY . /app

# Install python deps
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create volume mount points
VOLUME ["/app/kuzu_db", "/app/vector_db"]

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
