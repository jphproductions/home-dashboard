# API Endpoints

Base URL: `http://localhost:8000`

## Implementation Notes (2025 Standards)

**All endpoints follow these modern patterns:**

- **HTTP Client Injection**: Routes use `Depends(get_http_client)` to receive shared `httpx.AsyncClient`
- **Connection Pooling**: Single client with `max_keepalive=5`, `max_connections=10` reused across requests
- **Error Handling**: Exception chaining with `raise ... from e` preserves stack traces
- **Resource Cleanup**: WebSocket connections use try/finally to guarantee cleanup
- **Type Safety**: Pydantic v2 models with proper Optional type hints

**Example Route Pattern:**
```python
@router.post("/action")
async def perform_action(
    client: httpx.AsyncClient = Depends(get_http_client)
):
    result = await service_function(client)
    return result
```

## Health & Status

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

## Weather

### GET /api/weather/current
Get current weather conditions.

**Response:**
```json
{
  "temp": 12.5,
  "feels_like": 11.2,
  "condition": "Partly Cloudy",
  "icon": "02d",
  "location": "Den Bosch",
  "recommendation": "Light jacket recommended"
}
```

## Spotify

### GET /api/spotify/status
Get currently playing track and playback status.

**Response:**
```json
{
  "is_playing": true,
  "track_name": "Song Title",
  "artist_name": "Artist Name",
  "device_name": "TV Woonkamer",
  "progress_ms": 45000,
  "duration_ms": 240000
}
```

### POST /api/spotify/play
Resume playback.

**Response:**
```json
{
  "status": "playing"
}
```

### POST /api/spotify/pause
Pause playback.

**Response:**
```json
{
  "status": "paused"
}
```

### POST /api/spotify/next
Skip to next track.

**Response:**
```json
{
  "status": "skipped"
}
```

### POST /api/spotify/previous
Go to previous track.

**Response:**
```json
{
  "status": "previous"
}
```

### POST /api/spotify/wake-and-play
Wake TV and transfer current playback to TV device.

**Response:**
```json
{
  "status": "transferring",
  "detail": "TV woken and playback transferred"
}
```

## TV (Tizen)

### POST /api/tv/wake
Send KEY_POWER to wake TV (toggle power).

**Response:**
```json
{
  "status": "wake_sent",
  "detail": "KEY_POWER sent to TV"
}
```

### GET /api/tv/status
Get TV power status (experimental).

**Response:**
```json
{
  "power_on": true
}
```

## Phone (IFTTT)

### POST /api/phone/ring
Ring Jamie's phone via IFTTT webhook.

**Request:**
```json
{
  "message": "Ring from dashboard"
}
```

**Response:**
```json
{
  "status": "ring_sent",
  "detail": "Ring request sent to Jamie's phone"
}
```

## Error Responses

All errors return:
```json
{
  "detail": "Error message",
  "error_code": "ERROR_TYPE"
}
```

HTTP Status Codes:
- `200`: Success
- `400`: Bad Request
- `500`: Internal Server Error
