# ARK95X Unified Sovereign Stack - Dockerfile
# Python 3.11 + FastAPI + CrewAI + all dependencies

FROM python:3.11-slim

# Build args
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

LABEL maintainer="Ark95x-sAn" \
      version="${VERSION}" \
      description="ARK95X Unified Sovereign Stack Core API" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user (non-root)
RUN groupadd -r ark95x && useradd -r -g ark95x ark95x

# Set workdir
WORKDIR /app

# Install Python dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Set ownership
RUN chown -R ark95x:ark95x /app

# Switch to non-root user
USER ark95x

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]
