# Development Notes

## Quick Setup

1. Clone repo:
   \`\`\`bash
   git clone https://github.com/your-username/home-dashboard.git
   cd home-dashboard
   \`\`\`

2. Set up environment:
   \`\`\`bash
   cp .env.example .env
   # Edit .env with your values
   \`\`\`

3. Install dependencies:
   \`\`\`bash
   cd api_app && poetry install
   cd ../ui_app && poetry install
   cd ..
   \`\`\`

## Running Tests

```bash
# Unit tests (fast, offline)
pytest tests/unit

# Modern unit tests with AsyncMock
pytest tests/unit/api_app/test_weather_service_modern.py -v
pytest tests/unit/api_app/test_spotify_service_modern.py -v

# Integration tests (may require mocks)
pytest tests/integration

# Modern integration tests with dependency injection
pytest tests/integration/test_api_routes_modern.py -v

# All tests
pytest

# With coverage
pytest --cov=api_app --cov=ui_app
```

## Running Locally

### Option 1: Bare Python (Two terminals)

**Terminal 1 - FastAPI:**
```bash
cd api_app
poetry run uvicorn api_app.main:app --reload
```

**Terminal 2 - Streamlit:**
```bash
cd ui_app
poetry run streamlit run ui_app/app.py
```

Then open http://localhost:8501

### Option 2: Docker (Single command)

```bash
docker compose -f docker/docker-compose.yml up
```

Then open http://localhost:8501

## Adding a New Feature

### Checklist

1. **Define API contract** in `/api_app/api_app/models.py`
   - Request/response Pydantic models

2. **Implement service** in `/api_app/api_app/services/<feature>_service.py`
   - Pure Python business logic
   - Accept `httpx.AsyncClient` as first parameter
   - Use exception chaining: `raise CustomError(...) from e`
   - Add try/finally for resource cleanup (WebSockets, files, etc.)
   - Mock external APIs in tests with `AsyncMock`

3. **Add router** in `/api_app/api_app/routers/<feature>.py`
   - HTTP endpoints
   - Inject HTTP client: `client: httpx.AsyncClient = Depends(get_http_client)`
   - Call service functions with injected client
   - Handle errors → HTTP responses

4. **Include router** in `/api_app/api_app/main.py`
   - Add `app.include_router(...)` line

5. **Write tests**
   - Unit test in `tests/unit/api_app/test_<feature>_service.py`
   - Integration test in `tests/integration/test_<feature>_routes.py`

6. **Add UI tile** in `/ui_app/ui_app/tiles/<feature>.py`
   - Create cached fetch function: `@st.cache_data(ttl=...)`
   - Create callback functions for actions (avoid `st.rerun()`)
   - Use `st.status()` containers for long operations
   - Clear cache after state-changing operations
   - Call API endpoint with proper error handling
   - Display results

7. **Include tile** in `/ui_app/ui_app/app.py`
   - Add column and render call

8. **Update docs**
   - Add endpoint to `docs/endpoints.md`
   - Add tile info to `docs/tiles.md`

### Example: Adding a new "Lights" feature

```python
# 1. models.py
class LightStatus(BaseModel):
    name: str
    is_on: bool
    brightness: int

# 2. services/lights_service.py
async def get_lights():
    # Call external lights API
    pass

async def toggle_light(name: str):
    # Send command
    pass

# 3. routers/lights.py
@router.get("/lights", response_model=list[LightStatus])
async def get_lights():
    return await lights_service.get_lights()

@router.post("/lights/{name}/toggle")
async def toggle_light(name: str):
    await lights_service.toggle_light(name)
    return {"status": "toggled"}

# 4. main.py
app.include_router(lights.router, prefix="/api", tags=["lights"])

# 5. tests/unit/api_app/test_lights_service.py
@pytest.mark.asyncio
async def test_get_lights():
    # Mock and test
    pass

# 6. ui_app/tiles/lights.py
def render_tile(api_base_url: str):
    # Call API and render
    pass

# 7. ui_app/app.py
with col_x:
    st.subheader("Lights")
    lights.render_tile(API_BASE_URL)

# 8. docs/endpoints.md + docs/tiles.md
# Add documentation
```

## Deployment to Raspberry Pi

### One-Time Setup

1. Flash Raspberry Pi OS 64-bit
2. Enable SSH and Docker
3. Clone repo:
   \`\`\`bash
   git clone https://github.com/your-username/home-dashboard.git ~/home-dashboard
   cd ~/home-dashboard
   \`\`\`

4. Copy environment:
   \`\`\`bash
   cp .env.example .env
   nano .env  # Edit with real values
   \`\`\`

5. Set up systemd services:
   \`\`\`bash
   sudo cp infra/systemd/*.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable kiosk-chromium docker-dashboard
   \`\`\`

### Deploy Updates

```bash
cd ~/home-dashboard
git pull
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d
```

## Debugging

### View API logs
```bash
docker compose logs -f api
```

### View UI logs
```bash
docker compose logs -f ui
```

### SSH into API container
```bash
docker exec -it home-dashboard-api bash
```

### Check TV connectivity
```bash
python
>>> import websockets
>>> # Test WebSocket connection to TV
```

### Check Spotify API
```bash
curl -H "Authorization: Bearer <TOKEN>" https://api.spotify.com/v1/me/player
```

## Performance Tips

- Keep service functions fast (external API calls are async)
- Mock external APIs in tests
- Use httpx with connection pooling for HTTP calls
- Consider caching weather data (updates every 10 min anyway)

## Code Quality

```bash
# Lint with ruff
ruff check api_app ui_app

# Format with ruff
ruff format api_app ui_app

# Type check (optional, requires mypy setup)
mypy api_app
