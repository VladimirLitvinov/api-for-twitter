import asyncio
import pytest

from typing import AsyncGenerator
from httpx import AsyncClient

from src.main import app
from src.models.users import User
from tests.database import engine_test, async_session_maker, Base


@pytest.fixture(autouse=True, scope="session")
async def init_models():
    """
    Удаление и создание таблиц перед тестом
    """
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session")
def event_loop(request):
    """
    Create an instance of the default event loop for each test case.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Асинхронный клиент для выполнения запросов
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
async def users():
    """
    Пользователи для тестирования
    """
    async with async_session_maker() as session:
        user_1 = User(username="test-user1", api_key="test-user1")
        user_2 = User(username="test-user2", api_key="test-user2")
        user_3 = User(username="test-user3", api_key="test-user3")

        user_1.following.append(user_2)
        user_2.following.append(user_1)

        session.add_all([user_1, user_2, user_3])
        await session.commit()

        return user_1, user_2, user_3
