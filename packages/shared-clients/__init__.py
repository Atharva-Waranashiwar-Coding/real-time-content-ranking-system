"""Shared HTTP clients for the real-time content ranking system."""

import httpx
from typing import Optional, Dict, Any


async def create_http_client(timeout: float = 10.0) -> httpx.AsyncClient:
    """Create an async HTTP client.
    
    Args:
        timeout: Request timeout in seconds
    
    Returns:
        Configured AsyncClient instance
    """
    return httpx.AsyncClient(timeout=timeout)


class ServiceClient:
    """Base client for inter-service communication."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        """Initialize service client.
        
        Args:
            base_url: Base URL for the service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = await create_http_client(self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Make GET request."""
        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        url = f"{self.base_url}{path}"
        return await self.client.get(url, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        """Make POST request."""
        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")
        url = f"{self.base_url}{path}"
        return await self.client.post(url, **kwargs)


__all__ = ["create_http_client", "ServiceClient"]
