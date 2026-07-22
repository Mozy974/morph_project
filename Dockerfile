# ==============================================================================
# MULTI-STAGE BUILD DOCKERFILE — ENTERPRISE SUPERAGENT (PRODUCTION GRADE)
# ==============================================================================

# STAGE 1: BUILDER
FROM python:3.10-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# STAGE 2: FINAL RUNTIME
FROM python:3.10-slim AS final

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.10/site-packages" \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc_dir

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /install /install

# Copy application source code
COPY . /app/

# Create non-root user for SecOps compliance
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /tmp/prometheus_multiproc_dir && \
    chown appuser:appuser /tmp/prometheus_multiproc_dir

USER appuser

EXPOSE 8000

# Production : Gunicorn avec workers Uvicorn pour la concurrence multiprocess
CMD ["gunicorn", "orchestrator.api:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
