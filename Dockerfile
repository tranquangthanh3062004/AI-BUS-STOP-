# Dockerfile - Multi-stage Production Build for Smart Bus Stop Kiosk AI Engine
FROM python:3.11-slim as base

# Prevent Python from writing pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy python dependency requirements
COPY pyproject.toml /app/

# Install python packages
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    pydantic-settings \
    networkx

# Copy application source code
COPY shared/ /app/shared/
COPY edge_ai/ /app/edge_ai/
COPY rag/ /app/rag/
COPY local_llm/ /app/local_llm/
COPY knowledge_base/ /app/knowledge_base/
COPY backend/ /app/backend/
COPY kiosk_ui/ /app/kiosk_ui/
COPY scripts/ /app/scripts/

# Create logs folder
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8000/api/status || exit 1

# Start FastAPI application server
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
