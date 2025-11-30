# Architecture

## Overview

Home Dashboard is a Raspberry Pi 5-based home control system with:
- **Backend**: FastAPI serving REST API
- **Frontend**: Streamlit web UI
- **Hardware**: 5" touch display, USB microphone
- **Runtime**: Docker containers on Raspberry Pi OS 64-bit

## Components

### Backend (FastAPI)

Services for external integrations:
- **Weather Service**: OpenWeatherMap API → weather tile
- **Spotify Service**: Spotify Web API → playback control
- **Tizen Service**: Samsung TV WebSocket → TV wake/control
- **IFTTT Service**: Webhook calls → phone notifications

### Frontend (Streamlit)

Interactive tiles displayed on 5" touch display:
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
2. **UI calls FastAPI endpoint** (e.g., `/api/spotify/wake-and-play`)
3. **FastAPI service** executes:
   - Wake TV via Tizen WebSocket
   - Transfer Spotify playback to TV device
4. **Response returned to UI** (success/error toast)
5. **UI refreshes** to show new state

## Key Design Decisions

- **Two containers**: Clean separation, independent restart/scaling
- **Environment variables**: All secrets and config via .env (not in image)
- **Mocked testing**: External API calls mocked in tests (fast, offline)
- **No nginx**: Direct localhost routing in Phase 1 (add reverse proxy later if needed)
- **Fire-and-forget IFTTT**: Async webhook calls, no confirmation needed
- **Best-effort TV control**: Tizen WebSocket unreliable; handle gracefully

## Future Enhancements

- Spotify fullscreen mode with playlist browsing
- TV power-state detection (experimental)
- Multi-arch Docker image builds in CI
- Nginx reverse proxy
- Face recognition via camera
- Error escalation (fail 5x → notify phone)
