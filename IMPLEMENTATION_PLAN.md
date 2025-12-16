# 🚀 HOME DASHBOARD - IMPLEMENTATION PLAN

**Created:** December 16, 2025
**Based on:** Technical Review by Sarah, Linus, Jurgen, Xander, Leonie
**Goal:** Pragmatic improvements for production-ready home dashboard

---

## 📋 OVERVIEW

This plan addresses **critical and high-value recommendations** from the technical review while avoiding over-engineering. Total estimated time: **8-12 hours** spread across 6 phases.

### ✅ What We're Implementing
- Docker stability & resource management
- Security improvements
- Code maintainability (refactor main.py)
- Service decoupling
- Frontend polish (semantic HTML, better HTMX, loading states)
- Auto-save Spotify token
- Dependency updates

### ❌ What We're Skipping (Over-Engineering for Home Use)
- Domain layers / hexagonal architecture
- Comprehensive test suite (0% → 70%)
- SQLite persistence for state
- WCAG 2.1 compliance
- Circuit breakers
- Prometheus metrics
- CI/CD pipelines
- Repository pattern

---

## 🎯 PHASE 1: QUICK WINS ⚡

**Estimated Time:** 1 hour
**Priority:** CRITICAL

### Docker/Deployment Improvements

#### ✅ Add Resource Limits (2 min)
**Expert:** Linus (Section 2.1)
**Issue:** No memory/CPU limits → OOM killer risk on Raspberry Pi

**File:** `docker/docker-compose.yml`

```yaml
services:
  dashboard:
    # ... existing config ...
    deploy:
      resources:
        limits:
          memory: 512M      # Prevent OOM on Pi
          cpus: '1.0'       # Fair CPU allocation
        reservations:
          memory: 256M      # Minimum guaranteed
```

#### ✅ Enable Log Rotation (2 min)
**Expert:** Linus (Section 2.2)
**Issue:** Unbounded logs → SD card write amplification → premature failure

**File:** `docker/docker-compose.yml`

```yaml
services:
  dashboard:
    # ... existing config ...
    logging:
      driver: "json-file"
      options:
        max-size: "10m"     # Max 10MB per file
        max-file: "3"       # Keep 3 files (30MB total)
```

#### ✅ Fix Healthcheck Interval (1 min)
**Expert:** Linus (Section 2.3)
**Issue:** 5-minute interval → slow failure detection

**File:** `docker/Dockerfile.api`

```dockerfile
# Change from:
HEALTHCHECK --interval=300s ...

# To:
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1
```

### Security Improvements

#### ✅ Generate Strong API Key (30 sec)
**Expert:** Jurgen (Section 3.1)
**Issue:** Weak API key → brute force risk

**Commands:**
```bash
# Generate new key
openssl rand -hex 32

# Update in .env
DASHBOARD_API_KEY=<generated-key-here>
```

#### ✅ Fix CORS Wildcard (3 min)
**Expert:** Jurgen (Section 3.3)
**Issue:** FastAPI doesn't support `192.168.178.*` wildcards

**File:** `home_dashboard/main.py`

```python
# Change from:
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Wildcards don't work!
    ...
)

# To:
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.178\.\d+):8000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Dependency Updates

#### ✅ Update Outdated Packages (30 min)
**Expert:** Review Section "Dependency Updates"
**Issue:** Outdated packages → missing security fixes & features

**Commands:**
```bash
# Check outdated packages
poetry show --outdated

# Update one-by-one (test after each!)
poetry update fastapi
# Test: poetry run python -m home_dashboard.main
poetry update uvicorn
# Test again
poetry update websockets
# Test again
poetry update httpx
poetry update python-json-logger
poetry update python-multipart
poetry update mypy
poetry update ruff

# Verify everything works
poetry run ruff check .
poetry run mypy .
```

**Expected Updates:**
- fastapi: 0.122.1 → 0.124.4
- uvicorn: 0.32.1 → 0.38.0
- websockets: 12.0 → 15.0.1
- httpx: 0.27.2 → 0.28.1

---

## 🔨 PHASE 2: REFACTOR MAIN.PY

**Estimated Time:** 2-3 hours
**Priority:** HIGH

**Expert:** Sarah (Section 1.1 "The 642-Line main.py Monster")
**Issue:** Single 642-line file → unmaintainable, merge conflicts, tight coupling

### Target Structure

```
home_dashboard/
  main.py                    # 20 lines: create_app() + run
  core/
    __init__.py
    app_factory.py           # create_app() function (app creation)
    lifespan.py              # Startup/shutdown logic
    middleware.py            # CORS, rate limit, trusted hosts, request counting
  routers/
    health_router.py         # /health, /debug endpoints (NEW)
    spotify_router.py        # (existing)
    tv_tizen_router.py       # (existing)
    weather_router.py        # (existing)
    phone_ifttt_router.py    # (existing)
    view_router.py           # (existing)
  middleware/
    __init__.py
    error_handlers.py        # Exception handlers
    logging_middleware.py    # Request/response logging
```

### Implementation Steps

#### Step 1: Create Directory Structure (5 min)
```bash
mkdir home_dashboard/core
mkdir home_dashboard/middleware
touch home_dashboard/core/__init__.py
touch home_dashboard/core/app_factory.py
touch home_dashboard/core/lifespan.py
touch home_dashboard/core/middleware.py
touch home_dashboard/middleware/__init__.py
touch home_dashboard/middleware/error_handlers.py
touch home_dashboard/middleware/logging_middleware.py
touch home_dashboard/routers/health_router.py
```

#### Step 2: Extract Lifespan Management (30 min)
**File:** `home_dashboard/core/lifespan.py`

Extract lines 110-230 from main.py:
- Startup logic (cache, http_client, state managers)
- Shutdown logic (cleanup)
- Move utility functions (url_redaction, should_redact_url)

#### Step 3: Extract Middleware Configuration (30 min)
**File:** `home_dashboard/core/middleware.py`

Extract lines 240-280 from main.py:
- CORS configuration
- TrustedHost middleware
- Rate limiter setup
- Request counting middleware

#### Step 4: Extract Exception Handlers (20 min)
**File:** `home_dashboard/middleware/error_handlers.py`

Extract lines 501-600 from main.py:
- DashboardException handler
- HTTPException handler
- General exception handler
- Rate limit handler

#### Step 5: Extract Request/Response Logging (20 min)
**File:** `home_dashboard/middleware/logging_middleware.py`

Extract lines 76-108 from main.py:
- Request logging middleware
- Response logging middleware

#### Step 6: Extract Health/Debug Endpoints (30 min)
**File:** `home_dashboard/routers/health_router.py`

Extract lines 300-500 from main.py:
- `/health` endpoint
- `/debug` endpoint
- HealthResponse, DetailedHealthResponse, DebugInfo models

Move models to `home_dashboard/models/api/` or keep with router.

#### Step 7: Create App Factory (30 min)
**File:** `home_dashboard/core/app_factory.py`

```python
def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    # Load settings
    settings = get_settings()

    # Create app
    app = FastAPI(
        title="Home Dashboard API",
        description="...",
        version=__version__,
        lifespan=lifespan,
        ...
    )

    # Configure middleware
    setup_middleware(app, settings)

    # Register exception handlers
    register_error_handlers(app)

    # Register routers
    register_routers(app)

    # Custom OpenAPI
    app.openapi = custom_openapi

    return app
```

#### Step 8: Simplify main.py (10 min)
**File:** `home_dashboard/main.py`

```python
"""Main entry point for Home Dashboard application."""

from home_dashboard.core.app_factory import create_app

# Create application
app = create_app()

if __name__ == "__main__":
    import uvicorn
    from home_dashboard.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "home_dashboard.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
```

#### Step 9: Test Everything (20 min)
```bash
# Run application
poetry run python -m home_dashboard.main

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/debug
curl http://localhost:8000/  # Should load dashboard

# Check logs for errors
tail -f logs/dashboard.log

# Run linters
poetry run ruff check .
poetry run mypy .
```

---

## 🔗 PHASE 3: SERVICE DECOUPLING

**Estimated Time:** 1-2 hours
**Priority:** HIGH

**Expert:** Leonie (Section 5.2 "Tight Coupling")
**Issue:** spotify_service imports tv_tizen_service directly → tight coupling, untestable

### Current Problem

**File:** `home_dashboard/services/spotify_service.py`
```python
from home_dashboard.services import tv_tizen_service  # BAD: Direct import

async def wake_tv_and_play(...):
    await tv_tizen_service.wake_tv(...)  # Tight coupling
```

### Solution: Dependency Injection

#### Step 1: Create Service Protocol (15 min)
**File:** `home_dashboard/services/__init__.py` or `home_dashboard/protocols.py`

```python
from typing import Protocol
import httpx

class TVServiceProtocol(Protocol):
    """Protocol for TV control services."""

    async def wake_tv(
        self,
        client: httpx.AsyncClient,
        settings: Settings,
    ) -> None:
        """Wake the TV."""
        ...
```

#### Step 2: Update spotify_service.py (30 min)
**File:** `home_dashboard/services/spotify_service.py`

```python
# Remove direct import
# from home_dashboard.services import tv_tizen_service  # DELETE THIS

# Add protocol import
from home_dashboard.protocols import TVServiceProtocol

# Update function signature
async def wake_tv_and_play(
    client: httpx.AsyncClient,
    auth_manager: SpotifyAuthManager,
    settings: Settings,
    tv_service: TVServiceProtocol,  # NEW: Accept any TV service
) -> dict:
    """Wake TV and start playing Spotify."""
    # Wake TV
    await tv_service.wake_tv(client, settings)

    # ... rest of function unchanged ...
```

#### Step 3: Update spotify_router.py (30 min)
**File:** `home_dashboard/routers/spotify_router.py`

```python
# Add import
from home_dashboard.services import tv_tizen_service

# Create dependency function
def get_tv_service():
    """Dependency to provide TV service."""
    return tv_tizen_service

# Update endpoint
@router.post("/wake-and-play")
async def wake_and_play_endpoint(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
    settings: Settings = Depends(get_settings),
    tv_service = Depends(get_tv_service),  # NEW: Inject dependency
):
    """Wake TV and play Spotify."""
    result = await spotify_service.wake_tv_and_play(
        client,
        auth_manager,
        settings,
        tv_service,  # NEW: Pass injected service
    )

    # ... rest unchanged ...
```

#### Step 4: Test Wake-and-Play (15 min)
```bash
# Start app
poetry run python -m home_dashboard.main

# Test endpoint
curl -X POST http://localhost:8000/api/spotify/wake-and-play \
  -H "Authorization: Bearer YOUR_API_KEY"

# Or use dashboard UI button
# Should: Wake TV → Start Spotify playback
```

---

## ✨ PHASE 4: FRONTEND POLISH

**Estimated Time:** 2-3 hours
**Priority:** MEDIUM

**Experts:** Xander (Sections 4.2, 4.3, 4.4)

### Part 1: Semantic HTML (30 min)

**Expert:** Xander (Section 4.2 "Poor Semantic HTML")
**Issue:** Everything is `<div>` → poor structure, harder to maintain

#### Update base.html
**File:** `home_dashboard/templates/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Home Dashboard{% endblock %}</title>
    <link rel="stylesheet" href="/static/style.css">
    <script src="https://unpkg.com/htmx.org@2.0.7"></script>
</head>
<body>
    <header>
        <h1>🏠 Home Dashboard</h1>
    </header>

    <main class="dashboard-grid">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

#### Update index.html
**File:** `home_dashboard/templates/index.html`

```html
{% extends "base.html" %}

{% block content %}
<!-- Weather Tile -->
<article id="weather-tile"
         class="weather-area tile-loader"
         aria-labelledby="weather-heading"
         hx-get="/tiles/weather"
         hx-trigger="load, every 600s">
    <div class="tile"><h2 id="weather-heading">Loading Weather...</h2></div>
</article>

<!-- Spotify Tile -->
<article id="spotify-tile"
         class="spotify-area tile-loader"
         aria-labelledby="spotify-heading"
         hx-get="/tiles/spotify"
         hx-trigger="load">
    <div class="tile"><h2 id="spotify-heading">Loading Spotify...</h2></div>
</article>

<!-- Phone Tile -->
<article id="phone-tile"
         class="phone-area tile-loader"
         aria-labelledby="phone-heading"
         hx-get="/tiles/phone"
         hx-trigger="load">
    <div class="tile"><h2 id="phone-heading">Loading Phone...</h2></div>
</article>

<!-- Quick Actions Tile -->
<article id="quick-actions-tile"
         class="actions-area tile-loader"
         aria-labelledby="actions-heading"
         hx-get="/tiles/quick-actions"
         hx-trigger="load">
    <div class="tile"><h2 id="actions-heading">Loading Quick Actions...</h2></div>
</article>

<!-- Status Bar -->
<footer id="status-tile"
        class="status-area tile-loader"
        hx-get="/tiles/status"
        hx-trigger="load, every 30s">
</footer>
{% endblock %}
```

### Part 2: Better HTMX Patterns (1 hour)

**Expert:** Xander (Section 4.3 "Suboptimal HTMX Patterns")
**Issue:** Everything uses `outerHTML` swap → nuclear option, full rebuilds

#### Identify Swap Targets

**Current:** All buttons use `hx-swap="outerHTML"` on `#spotify-tile`
**Problem:** Entire tile disappears/reappears → flickering, inefficient

**Better:** Target specific elements for updates

**File:** `home_dashboard/templates/tiles/spotify.html`

```html
<article id="spotify-tile" class="tile spotify-area">
    <h2 id="spotify-heading">🎵 Spotify</h2>

    {% if not authenticated %}
    <!-- Auth section stays as-is -->
    <div class="message info">...</div>
    {% else %}

    <!-- Playback status - update this independently -->
    <div id="playback-status">
        {% if track_name %}
        <div class="spotify-track-info">
            <strong>Now Playing:</strong><br>
            🎵 {{ track_name }}<br>
            {% if artist_name %}👤 {{ artist_name }}<br>{% endif %}
            {% if device_name %}📱 {{ device_name }}{% endif %}
        </div>
        {% else %}
        <div class="spotify-track-info caption">
            Nothing currently playing
        </div>
        {% endif %}
    </div>

    <!-- Playlist section -->
    <div class="spotify-section">
        <strong>Select Playlist:</strong>
        <div class="spotify-playlist-grid">
            <select id="playlist-select" name="playlist">
                <option value="">Select...</option>
                {% for playlist in playlists %}
                <option value="{{ playlist.uri }}">{{ playlist.name }}</option>
                {% endfor %}
            </select>
            <button
                class="button button-secondary button-nowrap"
                hx-post="/api/spotify/play-playlist-from-form"
                hx-include="#playlist-select"
                hx-target="#playback-status"
                hx-swap="innerHTML">
                ▶️ Play
            </button>
        </div>
    </div>

    <!-- Playback controls - update only status -->
    <div class="spotify-controls">
        <button
            class="button button-secondary"
            hx-post="/api/spotify/previous"
            hx-target="#playback-status"
            hx-swap="innerHTML">
            ⏮️ Previous
        </button>

        {% if is_playing %}
        <button
            class="button button-secondary"
            hx-post="/api/spotify/pause"
            hx-target="#playback-status"
            hx-swap="innerHTML">
            ⏸️ Pause
        </button>
        {% else %}
        <button
            class="button button-secondary"
            hx-post="/api/spotify/play"
            hx-target="#playback-status"
            hx-swap="innerHTML">
            ▶️ Play
        </button>
        {% endif %}

        <button
            class="button button-secondary"
            hx-post="/api/spotify/next"
            hx-target="#playback-status"
            hx-swap="innerHTML">
            ⏭️ Next
        </button>
    </div>

    <!-- Wake TV & Play -->
    <button
        class="button button-full-width"
        hx-post="/api/spotify/wake-and-play"
        hx-target="#playback-status"
        hx-swap="innerHTML">
        📺 Wake TV & Play
    </button>

    {% endif %}
</article>
```

**Note:** Some endpoints may need to return only the status fragment instead of full tile. Update routers if needed.

### Part 3: Loading Indicators (1 hour)

**Expert:** Xander (Section 4.4 "No Loading States")
**Issue:** No feedback during API calls → looks frozen

#### Add Loading Spinner CSS
**File:** `home_dashboard/static/style.css`

```css
/* Loading spinner */
.htmx-indicator {
    display: none;
}

.htmx-request .htmx-indicator {
    display: inline-block;
}

.spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Button loading state */
button.htmx-request {
    opacity: 0.7;
    cursor: wait;
}
```

#### Add Spinner to Buttons
**File:** `home_dashboard/templates/tiles/spotify.html`

```html
<!-- Example: Play button with loading indicator -->
<button
    class="button button-secondary"
    hx-post="/api/spotify/play"
    hx-target="#playback-status"
    hx-swap="innerHTML"
    hx-indicator="#loading-spinner">
    <span class="htmx-indicator spinner"></span>
    ▶️ Play
</button>

<!-- Or use global indicator -->
<div id="loading-spinner" class="htmx-indicator">
    <div class="spinner"></div>
    Loading...
</div>
```

#### Add Error Handling
**File:** `home_dashboard/templates/base.html`

```html
<script>
    // Handle HTMX errors
    document.body.addEventListener('htmx:responseError', function(event) {
        console.error('Request failed:', event.detail);
        // Could show a toast notification here
        alert('Something went wrong. Please try again.');
    });

    // Handle network errors
    document.body.addEventListener('htmx:sendError', function(event) {
        console.error('Network error:', event.detail);
        alert('Network error. Check your connection.');
    });
</script>
```

---

## 💾 PHASE 5: AUTO-SAVE SPOTIFY TOKEN

**Estimated Time:** 1-2 hours
**Priority:** MEDIUM

**Expert:** Jurgen (Section 3.4 "Refresh Token Displayed in Browser")
**Issue:** Token shown in browser → shoulder surfing, history leak

### Implementation

#### Step 1: Create .env Update Utility (30 min)
**File:** `home_dashboard/utils/env_updater.py` (new file)

```python
"""Utility for safely updating .env file."""

from pathlib import Path
from typing import Optional


def update_env_file(env_path: Path, key: str, value: str) -> None:
    """Update or add a key-value pair in .env file.

    Args:
        env_path: Path to .env file
        key: Environment variable name
        value: New value for the variable

    Raises:
        FileNotFoundError: If .env file doesn't exist
        PermissionError: If .env file is not writable
    """
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found at {env_path}")

    # Read current content
    lines = env_path.read_text(encoding="utf-8").splitlines()

    # Find and update the key
    updated = False
    for i, line in enumerate(lines):
        # Skip comments and empty lines
        if line.strip().startswith("#") or not line.strip():
            continue

        # Check if this line contains our key
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break

    # If key not found, append it
    if not updated:
        # Add blank line if file doesn't end with one
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(f"# Auto-saved Spotify refresh token")
        lines.append(f"{key}={value}")

    # Write back to file
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_env_path() -> Path:
    """Get path to .env file (project root)."""
    # From home_dashboard/utils/env_updater.py
    # Navigate to project root: ../../.env
    return Path(__file__).parent.parent.parent / ".env"
```

#### Step 2: Update Spotify OAuth Callback (30 min)
**File:** `home_dashboard/routers/spotify_router.py`

```python
# Add imports
from home_dashboard.utils.env_updater import update_env_file, get_env_path
from home_dashboard.logging_config import log_with_context

@router.get("/auth/callback")
async def auth_callback(
    code: str,
    state: str | None = None,
    auth_manager: SpotifyAuthManager = Depends(get_spotify_auth_manager),
):
    """Handle Spotify OAuth callback.

    Receives authorization code, exchanges for tokens, and auto-saves
    refresh token to .env file.
    """
    # Verify state to prevent CSRF
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Clean up used state
    del _oauth_states[state]
    _cleanup_expired_oauth_states()

    try:
        # Exchange code for tokens
        token_info = auth_manager.get_access_token(code)
        refresh_token = token_info.get("refresh_token")

        if not refresh_token:
            raise HTTPException(
                status_code=500,
                detail="No refresh token received from Spotify"
            )

        # Auto-save refresh token to .env
        try:
            env_path = get_env_path()
            update_env_file(env_path, "SPOTIFY_REFRESH_TOKEN", refresh_token)

            log_with_context(
                logger,
                "info",
                "Spotify refresh token saved to .env",
                event_type="spotify_auth_success",
            )

            success_message = """
                <h1>✅ Authentication Complete!</h1>
                <p>Refresh token has been automatically saved to .env</p>
                <p><strong>Please restart the application for changes to take effect.</strong></p>
                <p><a href="/">← Back to Dashboard</a></p>
            """

        except Exception as e:
            log_with_context(
                logger,
                "error",
                "Failed to save refresh token to .env",
                event_type="env_update_failed",
                error=str(e),
            )

            # Fall back to manual display
            success_message = f"""
                <h1>⚠️ Authentication Successful (Manual Save Required)</h1>
                <p>Could not automatically save token. Please manually add to .env:</p>
                <div class="token-box">
                    <code>SPOTIFY_REFRESH_TOKEN={refresh_token}</code>
                </div>
                <p>Error: {str(e)}</p>
            """

        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Spotify Authentication</title>
            <style>
                body {{ font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                h1 {{ color: #1DB954; }}
                .token-box {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; overflow-wrap: break-word; }}
                code {{ font-family: monospace; color: #d63384; }}
            </style>
        </head>
        <body>
            {success_message}
        </body>
        </html>
        """)

    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Spotify OAuth callback failed",
            event_type="spotify_auth_error",
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")
```

#### Step 3: Create utils Directory (if needed)
```bash
mkdir -p home_dashboard/utils
touch home_dashboard/utils/__init__.py
```

#### Step 4: Test OAuth Flow (30 min)
```bash
# Start app
poetry run python -m home_dashboard.main

# Navigate to auth login
# http://localhost:8000/api/spotify/auth/login

# Complete OAuth flow in browser
# Should see: "✅ Authentication Complete! Refresh token saved to .env"

# Verify token in .env
cat .env | grep SPOTIFY_REFRESH_TOKEN
# Should show the new token

# Restart app
# Token should be loaded and Spotify should work
```

---

## 🧹 PHASE 6: FINAL CLEANUP

**Estimated Time:** 30 minutes
**Priority:** LOW (Do after moving to Raspberry Pi)

**Expert:** Jurgen (Section 3.2 "SSL Verification Disabled")
**Issue:** `verify=False` → MITM vulnerability for ALL external APIs

### Remove Proxy Code

#### Step 1: Remove SSL Verification Bypass
**File:** `home_dashboard/main.py` (or `dependencies.py`)

```python
# REMOVE these lines:
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# In get_http_client():
# REMOVE:
if proxy:
    client = httpx.AsyncClient(
        verify=False,  # DELETE THIS!
        proxies=proxy,
        ...
    )

# REPLACE WITH:
client = httpx.AsyncClient(
    timeout=httpx.Timeout(...),
    limits=httpx.Limits(...),
    follow_redirects=True,
    event_hooks=event_hooks,
    # verify=True is default - HTTPS works normally
)
```

#### Step 2: Remove Proxy Environment Variables
**File:** `.env`

```bash
# REMOVE these lines:
# HTTP_PROXY=http://bng-proxy-a.bng.nl:8080
# HTTPS_PROXY=http://bng-proxy-a.bng.nl:8080
```

#### Step 3: Test External API Calls
```bash
# Test Spotify
curl -X GET http://localhost:8000/api/spotify/status

# Test Weather
curl -X GET http://localhost:8000/api/weather/current

# Test IFTTT (if configured)
curl -X POST http://localhost:8000/api/phone/ring
```

### Raspberry Pi Deployment

#### Step 1: Set .env Permissions
**Command (on Raspberry Pi):**
```bash
chmod 600 /path/to/home-dashboard/.env
chown hilbrands:hilbrands /path/to/home-dashboard/.env

# Verify
ls -la .env
# Expected: -rw------- 1 hilbrands hilbrands
```

#### Step 2: Verify Docker Compose Changes
```bash
# Pull latest image
docker-compose pull

# Restart with new config
docker-compose down
docker-compose up -d

# Check logs
docker-compose logs -f dashboard

# Verify resource limits
docker stats
# Should show memory limit: 512MB
```

---

## ✅ SUCCESS CRITERIA

### Phase 1 Complete When:
- [ ] Docker container has memory limit (512M)
- [ ] Log rotation enabled (max 30MB)
- [ ] Healthcheck runs every 30s
- [ ] Strong API key generated (64 characters)
- [ ] CORS regex pattern working
- [ ] All dependencies updated
- [ ] App starts without errors

### Phase 2 Complete When:
- [ ] `main.py` is < 50 lines
- [ ] `core/` directory exists with 3 files
- [ ] `middleware/` directory exists with 2 files
- [ ] `routers/health_router.py` exists
- [ ] `/health` and `/debug` endpoints work
- [ ] All tiles load correctly
- [ ] No import errors
- [ ] Linters pass (ruff, mypy)

### Phase 3 Complete When:
- [ ] `TVServiceProtocol` defined
- [ ] `spotify_service.py` doesn't import `tv_tizen_service`
- [ ] `spotify_router.py` injects TV service
- [ ] "Wake TV & Play" button works
- [ ] TV wakes and Spotify starts

### Phase 4 Complete When:
- [ ] Dashboard uses `<main>`, `<article>`, `<header>`, `<footer>`
- [ ] All tiles have `aria-labelledby`
- [ ] Buttons use `hx-swap="innerHTML"` where appropriate
- [ ] Loading spinners appear during API calls
- [ ] Error messages show when API fails
- [ ] No visual regressions

### Phase 5 Complete When:
- [ ] `utils/env_updater.py` created
- [ ] OAuth callback auto-saves token
- [ ] Token appears in `.env` after auth
- [ ] Success page no longer displays token
- [ ] Restart loads token correctly
- [ ] Spotify works after restart

### Phase 6 Complete When:
- [ ] `verify=False` removed from code
- [ ] Proxy environment variables removed
- [ ] All external APIs work (Spotify, Weather, IFTTT)
- [ ] `.env` has 600 permissions on Pi
- [ ] Docker stats show 512M memory limit

---

## 📊 PROGRESS TRACKING

| Phase | Status | Date Started | Date Completed | Notes |
|-------|--------|--------------|----------------|-------|
| Phase 1: Quick Wins | ⏳ Not Started | | | |
| Phase 2: Refactor main.py | ⏳ Not Started | | | |
| Phase 3: Service Decoupling | ⏳ Not Started | | | |
| Phase 4: Frontend Polish | ⏳ Not Started | | | |
| Phase 5: Auto-save Token | ⏳ Not Started | | | |
| Phase 6: Final Cleanup | ⏳ Not Started | | | |

### Legend:
- ⏳ Not Started
- 🔄 In Progress
- ✅ Complete
- ⚠️ Blocked
- ❌ Skipped

---

## 🎓 CROSS-REFERENCE TO REVIEW

### Sarah (Project Structure & Maintainability)
- [x] Section 1.1: 642-Line main.py → **Phase 2**
- [ ] Section 1.2: Missing Directories → **Skipped** (over-engineering)
- [ ] Section 1.3: In-Memory State → **Skipped** (tolerable for home use)

### Linus (Hardware & Networking)
- [x] Section 2.1: No Resource Limits → **Phase 1**
- [x] Section 2.2: SD Card Write Amplification → **Phase 1**
- [x] Section 2.3: Healthcheck Interval → **Phase 1**
- [ ] Section 2.4: TV IP Validation → **Skipped** (nice-to-have)
- [ ] Section 2.5: HTTP Timeouts → **Skipped** (current values OK)
- [ ] Section 2.6: Circuit Breaker → **Skipped** (over-engineering)

### Jurgen (Security)
- [x] Section 3.1: Plaintext Secrets → **Phase 1** (chmod 600 on Pi)
- [x] Section 3.2: SSL Verification Disabled → **Phase 6**
- [x] Section 3.3: CORS Wildcard → **Phase 1**
- [x] Section 3.4: Refresh Token Displayed → **Phase 5**
- [ ] Section 3.5: No Account Lockout → **Skipped** (home network)

### Xander (Frontend)
- [x] Section 4.2: Poor Semantic HTML → **Phase 4**
- [x] Section 4.3: Suboptimal HTMX → **Phase 4**
- [x] Section 4.4: No Loading States → **Phase 4**
- [ ] Section 4.1: Zero Accessibility → **Partially** (semantic HTML only)
- [ ] Section 4.5: No Error Handling → **Phase 4** (basic only)
- [ ] Section 4.6: CDN Single Point → **Skipped** (acceptable risk)

### Leonie (Architecture)
- [x] Section 5.2: Tight Coupling → **Phase 3**
- [ ] Section 5.1: Missing Data Layer → **Skipped** (no DB needed)
- [ ] Section 5.3: No Domain Layer → **Skipped** (over-engineering)
- [ ] Section 5.4: Polling vs Event-Driven → **Skipped** (polling is fine)
- [ ] Section 5.5: No API Abstraction → **Skipped** (over-engineering)

### Dependency Updates
- [x] Update Packages → **Phase 1**

---

## 📝 NOTES

### Why We're Skipping Certain Items

**Tests (70% coverage):**
- Single user (yourself)
- Test by using it
- Would take 40-60 hours
- Not cost-effective for home project

**SQLite Persistence:**
- Re-auth on restart is tolerable
- Adds complexity (migrations, queries)
- 20+ hours implementation
- Not worth it unless restart is frequent

**WCAG Compliance:**
- You're the only user
- Unless you need screen reader, skip
- 20+ hours for full compliance

**Circuit Breakers:**
- Home network is stable
- TV is 3 feet away
- Over-engineering for local services

**Metrics/Monitoring:**
- Structured logs are sufficient
- Prometheus overkill for single Pi
- Check logs if issues occur

**CI/CD Pipeline:**
- Deploy manually from dev machine
- No team, no need for automation
- GitHub Actions would be nice-to-have

---

## 🚀 GETTING STARTED

1. **Review this plan** - Understand each phase
2. **Set up workspace** - Ensure you have:
   - Poetry installed
   - Docker + docker-compose
   - Code editor (VS Code recommended)
3. **Create feature branch** - `git checkout -b refactor/production-ready`
4. **Start with Phase 1** - Quick wins build momentum
5. **Test after each phase** - Don't accumulate untested changes
6. **Commit frequently** - Small commits easier to review/rollback
7. **Update progress table** - Track what's done

---

## 📞 HELP & REFERENCES

### If You Get Stuck

**Phase 2 (Refactor main.py):**
- Reference: FastAPI app factory pattern
- Example: <https://github.com/zhanymkanov/fastapi-best-practices>

**Phase 3 (Service Decoupling):**
- Reference: Python Protocols
- Docs: <https://docs.python.org/3/library/typing.html#typing.Protocol>

**Phase 4 (Frontend):**
- HTMX docs: <https://htmx.org/docs/>
- Semantic HTML guide: <https://developer.mozilla.org/en-US/docs/Glossary/Semantics>

**Phase 5 (Auto-save token):**
- Python pathlib: <https://docs.python.org/3/library/pathlib.html>
- File I/O: <https://docs.python.org/3/tutorial/inputoutput.html>

---

**Let's build something great! 🎉**
