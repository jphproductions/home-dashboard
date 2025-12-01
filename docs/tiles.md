# Tiles

Dashboard display is composed of interactive tiles, each controlling a system.

## Weather Tile

**Display:**
- Current temperature
- Feels-like temperature
- Condition icon
- Location (Den Bosch)
- One-line clothing/activity recommendation

**Calls:**
- GET /api/weather/current

**Refresh:** Every 10 minutes (cached with `@st.cache_data(ttl=600)`)

**Implementation (2025):**
- `fetch_weather_data()` cached function prevents excessive API calls
- Status container shows "Fetching weather data..." during load
- Cache automatically expires after 10 minutes
- Error handling with proper exception messages

**Assumptions:**
- OpenWeatherMap API key is valid
- Latitude/longitude are set correctly in config

## Spotify Tile

**Display (Compact):**
- Currently playing track name
- Artist name
- Device name (e.g., "TV Woonkamer")
- Play/Pause button
- Previous / Next buttons
- Mute button
- "Wake TV & Play" button

**Fullscreen Mode (Not in Phase 1):**
- Browse playlists
- Search for tracks/artists
- Select moods/mixes
- Transfer to TV and play

**Calls:**
- GET /api/spotify/status
- POST /api/spotify/play
- POST /api/spotify/pause
- POST /api/spotify/next
- POST /api/spotify/previous
- POST /api/spotify/wake-and-play

**Refresh:** On-demand (button press) + 5-second cache for status

**Implementation (2025):**
- `fetch_spotify_status()` cached for 5 seconds (`@st.cache_data(ttl=5)`)
- All buttons use `on_click=spotify_action` callback (no manual `st.rerun()`)
- Cache cleared after actions: `st.cache_data.clear()` ensures fresh data
- Status container shows feedback during wake-and-play operation
- Button parameters passed via `args=("play",)` pattern

**Assumptions:**
- Spotify Premium account (required for device transfer)
- TV is on same LAN and reachable
- TV has Spotify app running (or will auto-launch after wake)

## Phone Tile

**Display:**
- Large "Ring Jamie's Phone" button

**Calls:**
- POST /api/phone/ring

**Behavior:**
- Fire-and-forget (no confirmation)
- Shows "Ring request sent!" toast on success

**Assumptions:**
- Jamie has IFTTT app installed on phone
- IFTTT applet is set up for phone ring trigger
- IFTTT webhook key is correct

## Quick Actions Tile

**Display:**
- Buttons for shortcuts (Recipes, Transit, Calendar)

**Calls:**
- None (external links only)

**Status:**
- Placeholder in Phase 1

## Status Bar

**Display:**
- Last refresh timestamp
- System status indicator
- Manual refresh button

**Calls:**
- None (client-side only)

**Updates:**
- On every tile refresh
- On manual refresh button press
