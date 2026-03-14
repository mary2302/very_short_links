from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import get_settings

settings = get_settings()

# Создание асинхронного движка
engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)

# Создание асинхронной сессии
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Базовый класс для моделей
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Зависимость для получения асинхронной сессии базы данных."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Создает все таблицы в базе данных, определенные в моделях."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Удаляет все таблицы из базы данных."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
