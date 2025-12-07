#!/bin/bash

# Start Home Dashboard (FastAPI with HTMX frontend)
cd /app/home_dashboard
poetry run uvicorn home_dashboard.main:app --host 0.0.0.0 --port 8000
