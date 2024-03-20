from loguru import logger
import asyncio

from src.database import async_session_maker, engine, Base
from src.models.models import User, Tweet, Like, Image

users = [
    {
        "username": "Владимир",
        "api_key": "test",
    },
    {
        "username": "Ирина",
        "api_key": "test2",
    },
    {
        "username": "Михаил",
        "api_key": "test3",
    },
]

images = [
    {
        "tweet_id": 1,
        "path_media": "images/tweets/migrations_img/1.jpeg",
    },
    {
        "tweet_id": 2,
        "path_media": "images/tweets/migrations_img/2.jpg",
    }
]

tweets = [
    {
        "tweet_data": "Сложно, помогите...",
        "user_id": 1,
    },
    {
        "tweet_data": "Я идентифицирую себя как боевой вертолет КА-52",
        "user_id": 2,
    },
    {
        "tweet_data": "Всем привет!",
        "user_id": 3,
    }
]

likes = [
    {
        "user_id": 2,
        "tweets_id": 1,
    },
    {
        "user_id": 1,
        "tweets_id": 2,
    },
    {
        "user_id": 3,
        "tweets_id": 2,
    },
    {
        "user_id": 1,
        "tweets_id": 3,
    },
    {
        "user_id": 2,
        "tweets_id": 3,
    }
]


async def re_creation_db():
    """
    Удаление и создание БД
    """
    logger.debug("Создание БД")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Удаление всех таблиц
        await conn.run_sync(Base.metadata.create_all)  # Создание всех таблиц


async def migration_data():
    """
    Функция для наполнения БД демонстрационными данными
    """
    logger.debug("Загрузка демонстрационных данных")

    await re_creation_db()

    async with async_session_maker() as session:
        initial_users = [User(**user) for user in users]
        session.add_all(initial_users)

        initial_users[0].following.extend([initial_users[1], initial_users[2]])
        initial_users[1].following.append(initial_users[0])
        initial_users[2].following.extend([initial_users[1], initial_users[0]])

        initial_tweets = [Tweet(**tweet) for tweet in tweets]
        session.add_all(initial_tweets)

        initial_images = [Image(**image) for image in images]
        session.add_all(initial_images)

        initial_likes = [Like(**like) for like in likes]
        session.add_all(initial_likes)

        await session.commit()

        logger.debug("Данные добавлены")


if __name__ == "__main__":
    asyncio.run(migration_data())
