# Home Dashboard

A Raspberry Pi 5 home control dashboard with FastAPI backend and HTMX frontend.
Controls TV (Tizen), Spotify, weather, and phone notifications.

## Features

- **Weather Tile**: Current conditions, temperature, wind, clothing recommendations
- **Spotify Tile**: Play/pause, track info, playlist selection, wake TV and play
- **Phone Tile**: Ring somebodies phone via IFTTT webhook
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

- Python 3.11+
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
   # Leave SPOTIFY_REFRESH_TOKEN empty for now - we'll get it in step 6
   ```

3. Install dependencies:

   ```bash
   poetry install
   cd ..
   ```

4. Start the server:

   ```bash
   poetry run uvicorn home_dashboard.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. **Get Spotify Refresh Token** (first time only):
   - Open browser to `http://localhost:8000/api/spotify/auth/login`
   - Authorize the app with Spotify
   - Copy the refresh token displayed on the callback page
   - Paste it into your `.env` file: `SPOTIFY_REFRESH_TOKEN=your_token_here`
   - Restart the server

6. Open browser to `http://localhost:8000` - your dashboard is ready!

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

Full interactive documentation available at `/docs` when server is running.

### Health & Monitoring

- **`/health`** - Basic health check (returns `{"status": "ok", "version": "0.3.0"}`)
  - Used by Docker healthcheck
- **`/health/live`** - Liveness probe (is app running?)
  - Always returns 200 if process is alive
  - Use for Kubernetes/Docker liveness probes
- **`/health/ready`** - Readiness probe (can serve traffic?)
  - Checks external dependencies (Weather API, Spotify auth)
  - Returns 200 if ready, 503 if not ready
  - Rate limited: 30/minute
  - Caches external checks for 60s
- **`/debug`** - System diagnostics (requires API key)
  - Shows version, uptime, auth status, cache stats, config
  - Protected endpoint for troubleshooting

### API Endpoints

See the `/docs`

### Authentication

Most API endpoints require Bearer token authentication. Get your API key from `.env` file.

### Rate Limits

- Most endpoints: 60 requests/minute per IP
- Phone ring: 5 requests/minute (abuse prevention)
- Spotify play/pause: 30 requests/minute
- Health ready: 30 requests/minute

## Interactive API Docs

Visit **`http://localhost:8000/docs`** for full interactive API documentation with:

- Request/response examples
- "Try it out" functionality
- Authentication support
- Full endpoint descriptions

**Using `/docs` (Swagger UI):**

1. Click the **"Authorize"** 🔓 button at the top
2. Enter your API key (without "Bearer" prefix)
3. All "Try it out" requests will auto-include auth

**Using curl:**

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/api/phone/ring
```

## Contributing

This is a personal home project, but feel free to fork and customize!

## License

MIT
