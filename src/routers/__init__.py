"""Routers package initialization."""

from src.routers.auth import router as auth_router
from src.routers.links import router as links_router

__all__ = ["auth_router", "links_router"]
