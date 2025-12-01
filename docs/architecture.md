# Architecture

## Overview

Home Dashboard is a Raspberry Pi 5-based home control system with:
- **Backend**: FastAPI serving REST API
- **Frontend**: Streamlit web UI
- **Hardware**: 5" touch display, USB microphone
- **Runtime**: Docker containers on Raspberry Pi OS 64-bit

## Components

### Backend (FastAPI)

**Modern Patterns (2025):**
- **Lifespan Management**: `@asynccontextmanager` for startup/shutdown of HTTP client pool
- **Connection Pooling**: Shared `httpx.AsyncClient` with `max_keepalive=5`, `max_connections=10`
- **Dependency Injection**: `Depends(get_http_client)` pattern for injecting HTTP client into routes
- **Pydantic v2**: `SettingsConfigDict` for configuration management
- **Error Handling**: Exception chaining with `raise ... from e` for better debugging

**Services for external integrations:**
- **Weather Service**: OpenWeatherMap API → weather tile
- **Spotify Service**: Spotify Web API → playback control
- **Tizen Service**: Samsung TV WebSocket → TV wake/control
- **IFTTT Service**: Webhook calls → phone notifications

### Frontend (Streamlit)

**Modern Patterns (2025):**
- **Caching**: `@st.cache_data(ttl=...)` to reduce API calls (weather: 10min, Spotify: 5sec)
- **Callbacks**: `on_click` handlers instead of `st.rerun()` for better UX
- **Status Containers**: `st.status()` for long-running operations feedback
- **Cache Clearing**: `st.cache_data.clear()` after state-changing operations

**Interactive tiles displayed on 5" touch display:**
- **Weather Tile**: Display current conditions + recommendation
- **Spotify Tile**: Playback controls, track info, wake TV & play
- **Phone Tile**: Fire-and-forget button to ring Jamie's phone
- **Quick Actions**: Placeholder links (recipes, transit, calendar)
- **Status Bar**: Last refresh timestamp

### Infrastructure

- **Docker Containers**: API and UI in separate containers via docker-compose
- **Systemd Services**: Kiosk mode Chromium auto-start, container management
- **Network**: Local LAN only (no cloud, no port forwarding needed)

## Data Flow

1. **User interacts with Streamlit UI** (tap button on 5" display)
2. **UI callback function triggered** (e.g., `spotify_action("wake-and-play")`)
3. **Cached data checked** - if fresh, return immediately; if stale, proceed
4. **UI calls FastAPI endpoint** (e.g., `/api/spotify/wake-and-play`)
5. **FastAPI router** injects shared HTTP client via `Depends(get_http_client)`
6. **Service function** executes with injected client:
   - Wake TV via Tizen WebSocket (try/finally ensures cleanup)
   - Transfer Spotify playback to TV device
7. **Response returned to UI** (success/error toast in status container)
8. **Cache cleared** for affected data (e.g., Spotify status)
9. **UI redraws automatically** via callback mechanism (no manual rerun)

## Key Design Decisions

- **Two containers**: Clean separation, independent restart/scaling
- **Environment variables**: All secrets and config via .env (not in image)
- **Connection pooling**: Single shared HTTP client for all requests (reduces overhead)
- **Dependency injection**: HTTP client injected into routes (testable, maintainable)
- **Smart caching**: Weather cached 10min, Spotify 5sec (reduces API calls without stale data)
- **Callback-driven UI**: No manual reruns, cleaner state management
- **Mocked testing**: External API calls mocked with AsyncMock in tests (fast, offline)
- **No nginx**: Direct localhost routing in Phase 1 (add reverse proxy later if needed)
- **Fire-and-forget IFTTT**: Async webhook calls, no confirmation needed
- **Best-effort TV control**: Tizen WebSocket unreliable; handle gracefully with try/finally

## Future Enhancements

- Spotify fullscreen mode with playlist browsing
- TV power-state detection (experimental)
- Multi-arch Docker image builds in CI
- Nginx reverse proxy
- Face recognition via camera
- Error escalation (fail 5x → notify phone)
