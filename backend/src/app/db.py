from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.settings import get_settings


@asynccontextmanager
async def db_session():
    # Putting engine creation and sessionmaker in here
    # so that importing app.db doesn't trigger get_settings().
    # TODO: determine best syntax to use for engine/sessionmaker
    engine = create_async_engine(get_settings().DB_DSN)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session()
    try:
        yield session
        await session.commit()
    finally:
        await session.close()
