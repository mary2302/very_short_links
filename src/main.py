from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import create_tables, get_db
from src.routers import auth_router, links_router
from src.services.cache_service import get_cache_service, CacheService
from src.services.link_service import LinkService
from src.utils.url_helpers import get_base_url

# Получение настроек приложения
settings = get_settings()

# Rate limiter для ограничения количества запросов
limiter = Limiter(key_func=get_remote_address)


def get_link_service(
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
) -> LinkService:
    """Dependency для получения экземпляра LinkService с доступом к базе данных и кэшу."""
    return LinkService(db, cache)


@asynccontextmanager # Декоратор контекстного менеджера для асинхронного управления ресурсами
async def lifespan(app: FastAPI):
    """Обработчик жизненного цикла приложения для управления ресурсами."""
    # Startup
    await create_tables()
    cache = await get_cache_service()
    yield
    # Shutdown
    await cache.disconnect()

# Инициализация FastAPI приложения с указанием обработчика жизненного цикла
app = FastAPI(
    title="Very short links",
    description="A FastAPI service for creating and managing shortened URLs",
    version="1.0.0",
    lifespan=lifespan,
)

# Добавление rate limiter в состояние приложения для использования в роутерах
app.state.limiter = limiter


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Обработчик исключения для случаев превышения лимита запросов, возвращает 429 статус с сообщением."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"}
    )


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS настройки для разрешения запросов с указанных источников, поддержка всех методов и заголовков, а также учет учетных данных (cookies, авторизационные заголовки и т.д.) при кросс-доменных запросах.
app.add_middleware(
    CORSMiddleware, # CORS middleware для управления кросс-доменными запросами
    allow_origins=settings.cors_origins, # Разрешенные источники для CORS
    allow_credentials=True, # Разрешить отправку учетных данных (cookies, авторизационные заголовки и т.д.) при кросс-доменных запросах
    allow_methods=["GET", "POST", "PUT", "DELETE"], # Разрешенные HTTP методы для CORS
    allow_headers=["*"], # Разрешить все заголовки для CORS
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
    link_service: LinkService = Depends(get_link_service)
):
    """
    Перенаправление на оригинальный URL.
    
    - **short_code**: Короткий код или пользовательский псевдоним для перенаправления
    
    Этот endpoint обрабатывает перенаправление от короткой ссылки к оригинальной URL.
    """
    # Защита от попыток доступа к зарезервированным путям, которые не должны обрабатываться как короткие коды
    if short_code in ["links", "auth", "docs", "redoc", "openapi.json", "health"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid short code"
        )
    
    # Получение базового URL для формирования полного URL при перенаправлении
    base_url = get_base_url(request) 
    original_url = await link_service.get_original_url(short_code, base_url)
    base_url = str(request.base_url).rstrip("/") 
    original_url = await link_service.get_original_url(short_code, base_url)
    
    # Если оригинальный URL не найден или ссылка истекла, возвращаем 404 ошибку
    if original_url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found or expired"
        )
    
    return RedirectResponse(url=original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

# Точка входа для запуска приложения
if __name__ == "__main__":
    import uvicorn 
    # Запуск приложения с помощью Uvicorn ASGI сервера
    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
