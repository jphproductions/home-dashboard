# syntax=docker/dockerfile:1

# ============================================
# Stage 1: Builder
# ============================================

FROM python:3.12-slim AS builder

WORKDIR /code

# Install Poetry
RUN pip install --no-cache-dir poetry==2.1.3

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Create .venv
RUN poetry config virtualenvs.in-project true

# Install dependencies
RUN poetry install --only main --no-root --no-interaction --no-ansi

# ============================================
# Stage 2: Runtime
# ============================================

FROM python:3.12-slim AS runtime

WORKDIR /code

# Install curl
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy project
COPY --from=builder /code/.venv /code/.venv
COPY home_dashboard /code/home_dashboard
COPY playlists.json /code/playlists.json

# Create non-root user for security
RUN groupadd -r dashboard && useradd -r -g dashboard dashboard && \
    chown -R dashboard:dashboard /code
USER dashboard

# Set Python environment
ENV PATH="/code/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port 8000
EXPOSE 8000

# Health check using curl
HEALTHCHECK --interval=300s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with Uvicorn
CMD ["uvicorn", "home_dashboard.main:app", "--host", "0.0.0.0", "--port", "8000"]
