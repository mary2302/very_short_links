from fastapi import Request


def get_base_url(request: Request) -> str:
    """Получает базовый URL из объекта запроса"""
    return str(request.base_url).rstrip("/")
