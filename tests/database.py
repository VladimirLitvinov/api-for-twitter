from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.main import app
from src.database import Base, get_async_session
from src.config import DB_HOST, DB_NAME, DB_PASS, DB_USER, DB_PORT

DATABASE_URL_TEST = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine_test = create_async_engine(DATABASE_URL_TEST, poolclass=NullPool)

async_session_maker = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)

Base.metadata.bind = engine_test


async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


app.dependency_overrides[get_async_session] = override_get_async_session
