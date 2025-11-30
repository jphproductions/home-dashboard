"""Spotify API routes."""

from fastapi import APIRouter, HTTPException
from api_app.services import spotify_service
from api_app.models import SpotifyStatus

router = APIRouter()


@router.get("/status", response_model=SpotifyStatus)
async def get_spotify_status():
    """Get current Spotify playback status."""
    try:
        status = await spotify_service.get_current_track()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}")


@router.post("/play")
async def play():
    """Resume playback."""
    try:
        await spotify_service.play()
        return {"status": "playing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}")


@router.post("/pause")
async def pause():
    """Pause playback."""
    try:
        await spotify_service.pause()
        return {"status": "paused"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}")


@router.post("/next")
async def next_track():
    """Skip to next track."""
    try:
        await spotify_service.next_track()
        return {"status": "skipped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}")


@router.post("/previous")
async def previous_track():
    """Go to previous track."""
    try:
        await spotify_service.previous_track()
        return {"status": "previous"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify error: {str(e)}")


@router.post("/wake-and-play")
async def wake_tv_and_play():
    """Wake TV and transfer current playback."""
    try:
        result = await spotify_service.wake_tv_and_play()
        return {"status": "transferring", "detail": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wake/Play error: {str(e)}")
