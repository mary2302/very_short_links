from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import create_tables, get_db
from src.routers import auth_router, links_router
from src.services.cache_service import get_cache_service, CacheService
from src.services.link_service import LinkService

# Получение настроек приложения
settings = get_settings()


@asynccontextmanager # Декоратор контекстного менеджера для асинхронного управления ресурсами
async def lifespan(app: FastAPI):
    """Обработчик жизненного цикла приложения для управления ресурсами."""
    # Startup
    await create_tables()
    cache = await get_cache_service()
    yield
    # Shutdown
    await cache.disconnect()


app = FastAPI(
    title="URL Shortener API",
    description="A FastAPI service for creating and managing shortened URLs",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - это 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров для аутентификации и управления ссылками
app.include_router(auth_router)
app.include_router(links_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint для проверки работоспособности API."""
    return {
        "message": "Welcome to URL Shortener API",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint для мониторинга состояния сервиса."""
    return {"status": "healthy"}


@app.get("/{short_code}", tags=["Redirect"])
async def redirect_to_original(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """
    Redirect to the original URL.
    
    - **short_code**: The short code or custom alias
    
    This endpoint handles the actual redirection from short URL to original URL.
    """
    # Skip if it looks like an API path
    if short_code in ["links", "auth", "docs", "redoc", "openapi.json", "health"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid short code"
        )
    
    link_service = LinkService(db, cache)
    base_url = str(request.base_url).rstrip("/")
    original_url = await link_service.get_original_url(short_code, base_url)
    
    if original_url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found or expired"
        )
    
    return RedirectResponse(url=original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


if __name__ == "__main__":
    import uvicorn
    # Запуск приложения с помощью Uvicorn ASGI сервера
    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
