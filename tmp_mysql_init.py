import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine import make_url
from backend.core.config import settings

async def main():
    url = make_url(settings.database_url)
    dbname = url.database
    if not dbname:
        raise SystemExit('DATABASE_URL must include a database name')
    base_url = url.set(database='')
    engine = create_async_engine(base_url, future=True, echo=False)
    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    await engine.dispose()
    print('database created or already exists:', dbname)

asyncio.run(main())
