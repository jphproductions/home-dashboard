# Home Dashboard

A Raspberry Pi 5 home control dashboard with FastAPI backend and HTMX frontend.
Controls TV (Tizen), Spotify, weather, and phone notifications.

## Features

- **Weather Tile**: Current conditions, temperature, wind, clothing recommendations
- **Spotify Tile**: Play/pause, track info, playlist selection, wake TV and play
- **Phone Tile**: Ring Jamie's phone via IFTTT webhook
- **Quick Actions**: Wake TV, power off TV
- **Status Bar**: Last refresh timestamp

## Architecture

- **Backend**: FastAPI (Python) running on port 8000
- **Frontend**: HTMX with Jinja2 templates
- **API**: Supports both JSON (REST) and HTML (HTMX) responses via `?format` parameter
- **Infrastructure**: Docker containers, systemd services for kiosk mode
- **Runtime**: Raspberry Pi 5 with 64-bit OS

## Quick Start (Local Development)

### Prerequisites

- Python 3.9+
- Poetry
- Docker (optional, for full setup)

### Setup

1. Clone the repo:

   ```bash
   git clone https://github.com/your-username/home-dashboard.git
   cd home-dashboard
   ```

2. Copy and fill environment:

   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys, TV IP, etc.
   ```

3. Install dependencies:

   ```bash
   cd home_dashboard && poetry install
   cd ..
   ```

4. Run tests:

   ```bash
   pytest
   ```

5. Start the server:

   ```bash
   cd home_dashboard && poetry run uvicorn home_dashboard.main:app --reload --host 127.0.0.1 --port 8000
   ```

6. Open browser to `http://localhost:8000`


## Raspberry Pi Deployment

### First Boot Setup

1. Flash Raspberry Pi OS 64-bit to microSD
2. Enable SSH and Docker
3. Clone repo to Pi
4. Fill `.env` with real values (TV IP, API keys)
5. Run Docker:

   ```bash
   docker compose up -d
   ```

6. Chromium kiosk will auto-start and display the dashboard

### Systemd Services

- `kiosk-chromium.service`: Starts Chromium in kiosk mode at boot
- `docker-dashboard.service`: Manages Docker container lifecycle (optional)

See [infra/systemd/](infra/systemd/) for configuration.

## API Documentation

Coming soon

Quick reference:

- `/` - Main dashboard page
- `/health` - Health check
- `/api/weather/current?format=json|html` - Current weather
- `/api/spotify/status?format=json|html` - Spotify status
- `/api/spotify/play?format=json|html` - Play music
- `/api/tv/wake` - Wake TV
- `/api/phone/ring?format=json|html` - Ring phone
- `/docs` - Interactive API documentation (Swagger UI)

## Development

### Running Tests

```bash
# Unit tests only (fast)
pytest tests/unit

# All tests
pytest

# With coverage
pytest --cov=home_dashboard
```

### Adding a Feature

Docs coming soon

## Contributing

This is a personal home project, but feel free to fork and customize!

## License

MIT
