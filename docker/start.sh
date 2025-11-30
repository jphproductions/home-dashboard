#!/bin/bash

# Start FastAPI in background
cd /app/api_app
poetry run uvicorn api_app.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit (foreground)
cd /app/ui_app
poetry run streamlit run ui_app/app.py --server.port=8501 --server.address=0.0.0.0
