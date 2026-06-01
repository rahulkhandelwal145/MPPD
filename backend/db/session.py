from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.config import settings


def get_engine():
    return create_async_engine(settings.database_url, future=True, echo=settings.debug)


engine = get_engine()
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True,
)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
