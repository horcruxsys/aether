# Multi-stage Dockerfile for nexus-manager
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv package manager
RUN pip install uv --no-cache-dir

# Copy pyproject.toml and lock file
COPY pyproject.toml ./
COPY uv.lock ./

# Build dependencies in isolated venv
RUN uv sync --frozen

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/

# Set Python path to use venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Create cache directory for Avro files and Qdrant storage
RUN mkdir -p /app/.cache

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
