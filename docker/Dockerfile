# syntax=docker/dockerfile:1

# ============================================
# Stage 1: Builder - Install dependencies
# ============================================
# Per Docker best practices: Use multi-stage builds to minimize final image size
FROM python:3.11-slim AS builder

WORKDIR /code

# Install Poetry
RUN pip install --no-cache-dir poetry==1.7.1

# Copy dependency files ONLY (leverage Docker layer caching)
COPY pyproject.toml poetry.lock ./

# ✅ Configure poetry to create virtual environment in project
RUN poetry config virtualenvs.in-project true

# ✅ Install dependencies to .venv directory (no Poetry needed at runtime)
RUN poetry install --only main --no-root --no-interaction --no-ansi

# ============================================
# Stage 2: Runtime - Minimal production image
# ============================================
FROM python:3.11-slim AS runtime

WORKDIR /code

# ✅ Install curl for health checks (more reliable than httpx)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ✅ Copy ONLY the virtual environment from builder (not Poetry!)
# This saves ~50MB by not including Poetry at runtime
COPY --from=builder /code/.venv /code/.venv

# Copy application code
COPY home_dashboard /code/home_dashboard
COPY playlists.json /code/playlists.json

# Create non-root user for security
RUN groupadd -r dashboard && useradd -r -g dashboard dashboard && \
    chown -R dashboard:dashboard /code

# Switch to non-root user
USER dashboard

# ✅ Set Python environment - use .venv directly
ENV PATH="/code/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port 8000
EXPOSE 8000

# ✅ Health check using curl (more reliable than httpx)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ✅ Run uvicorn directly (no need for "poetry run" since .venv/bin is in PATH)
CMD ["uvicorn", "home_dashboard.main:app", "--host", "0.0.0.0", "--port", "8000"]
