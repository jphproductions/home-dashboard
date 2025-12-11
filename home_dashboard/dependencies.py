"""FastAPI dependencies for dependency injection."""

import httpx
from fastapi import Request
from home_dashboard.state_managers import SpotifyAuthManager, TVStateManager


async def get_http_client(request: Request) -> httpx.AsyncClient:
    """
    Get the shared HTTP client from app state.
    
    This dependency provides access to the connection-pooled HTTP client
    initialized during application startup.
    
    Args:
        request: The FastAPI request object.
        
    Returns:
        The shared AsyncClient instance.
        
    Raises:
        RuntimeError: If HTTP client is not initialized.
    """
    client = request.app.state.http_client
    
    if client is None:
        raise RuntimeError("HTTP client not initialized. This should never happen.")
    
    return client


async def get_spotify_auth_manager(request: Request) -> SpotifyAuthManager:
    """
    Get the Spotify authentication manager from app state.
    
    This dependency provides access to the shared Spotify auth manager
    initialized during application startup.
    
    Args:
        request: The FastAPI request object.
        
    Returns:
        The shared SpotifyAuthManager instance.
        
    Raises:
        RuntimeError: If Spotify auth manager is not initialized.
    """
    manager = request.app.state.spotify_auth_manager
    
    if manager is None:
        raise RuntimeError("Spotify auth manager not initialized.")
    
    return manager


async def get_tv_state_manager(request: Request) -> TVStateManager:
    """
    Get the TV state manager from app state.
    
    This dependency provides access to the shared TV state manager
    initialized during application startup.
    
    Args:
        request: The FastAPI request object.
        
    Returns:
        The shared TVStateManager instance.
        
    Raises:
        RuntimeError: If TV state manager is not initialized.
    """
    manager = request.app.state.tv_state_manager
    
    if manager is None:
        raise RuntimeError("TV state manager not initialized.")
    
    return manager
