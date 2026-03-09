"""URL helper utilities."""

from fastapi import Request


def get_base_url(request: Request) -> str:
    """Get base URL from request."""
    return str(request.base_url).rstrip("/")
