# Multi-stage Dockerfile for FastAPI Control Plane
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Stage 1: Dependencies builder
FROM base AS builder
WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --upgrade pip && \
    pip install .

# Stage 2: Final runner
FROM base AS runner
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

# Run as non-root user with shared frame & enrollment storage permissions
RUN mkdir -p /data/frames /data/enrollments /app/models && \
    useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /data/frames /data/enrollments /app/models
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:create_application", "--factory", "--host", "0.0.0.0", "--port", "8000"]

