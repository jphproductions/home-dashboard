"""FastAPI dependencies for dependency injection."""

import httpx
from fastapi import Request


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
