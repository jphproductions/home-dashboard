# Home Dashboard

A Raspberry Pi 5 home control dashboard with Streamlit UI and FastAPI backend. 
Controls TV (Tizen), Spotify, weather, and phone notifications.

## Features

- **Weather Tile**: Current conditions, temperature, clothing recommendations
- **Spotify Tile**: Play/pause, track info, wake TV and play
- **Phone Tile**: Ring Jamie's phone via IFTTT webhook
- **Quick Actions**: Placeholder for links (recipes, transit, calendar)
- **Status Bar**: Last refresh timestamp

## Architecture

- **Backend**: FastAPI (Python) running on port 8000
- **Frontend**: Streamlit UI on port 8501
- **Infrastructure**: Docker containers, systemd services for kiosk mode
- **Runtime**: Raspberry Pi 5 with 64-bit OS

See [docs/architecture.md](docs/architecture.md) for detailed design.

## Quick Start (Local Development)

### Prerequisites

- Python 3.9+
- Poetry
- Docker (optional, for full setup)

### Setup

1. Clone the repo:
   \`\`\`bash
   git clone https://github.com/your-username/home-dashboard.git
   cd home-dashboard
   \`\`\`

2. Copy and fill environment:
   \`\`\`bash
   cp .env.example .env
   # Edit .env with your actual API keys, TV IP, etc.
   \`\`\`

3. Install dependencies:
   \`\`\`bash
   cd api_app && poetry install
   cd ../ui_app && poetry install
   cd ..
   \`\`\`

4. Run tests:
   \`\`\`bash
   pytest
   \`\`\`

5. Start services locally (two terminals):
   
   Terminal 1 (FastAPI):
   \`\`\`bash
   cd api_app && poetry run uvicorn api_app.main:app --reload
   \`\`\`
   
   Terminal 2 (Streamlit):
   \`\`\`bash
   cd ui_app && poetry run streamlit run ui_app/app.py
   \`\`\`

6. Open browser to `http://localhost:8501`

## Raspberry Pi Deployment

### First Boot Setup

1. Flash Raspberry Pi OS 64-bit to microSD
2. Enable SSH and Docker
3. Clone repo to Pi
4. Fill `.env` with real values (TV IP, API keys)
5. Run Docker:
   \`\`\`bash
   docker compose up -d
   \`\`\`

6. Chromium kiosk will auto-start and display the dashboard

### Systemd Services

- `kiosk-chromium.service`: Starts Chromium in kiosk mode at boot
- `docker-dashboard.service`: Manages Docker container lifecycle (optional)

See [infra/systemd/](infra/systemd/) for configuration.

## API Documentation

See [docs/endpoints.md](docs/endpoints.md) for complete API routes.

Quick reference:
- `/api/health` - Health check
- `/api/weather/current` - Current weather
- `/api/spotify/*` - Spotify controls and info
- `/api/tv/wake` - Wake TV
- `/api/phone/ring` - Ring Jamie's phone

## Development

### Running Tests

```bash
# Unit tests only (fast)
pytest tests/unit

# All tests
pytest

# With coverage
pytest --cov=api_app --cov=ui_app
```

### Adding a Feature

See [docs/dev-notes.md](docs/dev-notes.md) for step-by-step guide.

## Contributing

This is a personal home project, but feel free to fork and customize!

## License

MIT (or your choice)