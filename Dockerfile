# ==============================================================================
# HR Assistance AI Chatbot POC - Dockerfile
# ==============================================================================
FROM python:3.12-slim

# Optimize Python execution in container environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system utilities (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies in separate layer for fast Docker cache hits
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and documents into the image
COPY app/ ./app/
COPY data/documents/ ./data/documents/

# Ensure directory for persistent ChromaDB vector store exists
RUN mkdir -p /app/data/chroma_db

# Expose API port
EXPOSE 8000

# Docker healthcheck against the FastAPI /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
