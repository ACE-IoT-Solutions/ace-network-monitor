# Multi-stage build for ACE Connection Logger
# Stage 1: Build Vue.js frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ping
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY pyproject.toml ./

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Install Python dependencies
RUN uv pip install --system --no-cache -e .

# Copy Python application code
COPY *.py ./
COPY config.yaml ./

# Copy built frontend from stage 1
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Create directory for database
RUN mkdir -p /data

# Expose API port (default 8506, can be overridden)
EXPOSE 8506

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/data/connection_logs.db
ENV API_PORT=8506
ENV API_HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; import os; requests.get(f'http://localhost:{os.getenv(\"API_PORT\", 8506)}/health')" || exit 1

# Run the monitor command with API server
CMD python main.py monitor --api-host ${API_HOST} --api-port ${API_PORT}
