"""Spotify API routes."""

import httpx
from fastapi import APIRouter, Depends, HTTPException

from api_app.dependencies import get_http_client
from api_app.services import spotify_service
from shared.models.spotify import SpotifyStatus

router = APIRouter()


@router.get("/status", response_model=SpotifyStatus)
async def get_spotify_status(client: httpx.AsyncClient = Depends(get_http_client)):
    """Get current Spotify playback status."""
    try:
        status = await spotify_service.get_current_track(client)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/play")
async def play(client: httpx.AsyncClient = Depends(get_http_client)):
    """Resume playback."""
    try:
        await spotify_service.play(client)
        return {"status": "playing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/pause")
async def pause(client: httpx.AsyncClient = Depends(get_http_client)):
    """Pause playback."""
    try:
        await spotify_service.pause(client)
        return {"status": "paused"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/next")
async def next_track(client: httpx.AsyncClient = Depends(get_http_client)):
    """Skip to next track."""
    try:
        await spotify_service.next_track(client)
        return {"status": "skipped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/previous")
async def previous_track(client: httpx.AsyncClient = Depends(get_http_client)):
    """Go to previous track."""
    try:
        await spotify_service.previous_track(client)
        return {"status": "previous"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}") from e


@router.post("/wake-and-play")
async def wake_tv_and_play(client: httpx.AsyncClient = Depends(get_http_client)):
    """Wake TV and transfer current playback."""
    try:
        result = await spotify_service.wake_tv_and_play(client)
        return {"status": "transferring", "detail": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wake/Play error: {str(e)}") from e
