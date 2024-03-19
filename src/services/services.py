from http import HTTPStatus
from itertools import chain
from typing import List

from fastapi import UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from sqlalchemy.orm import joinedload, selectinload

from src.database import async_session_maker
from src.models.models import User, Image, Like, Tweet
from src.schemas.schemas import TweetInSchema
from src.utils.exeptions import CustomApiException
from src.utils.image import delete_images, save_image


class FollowerService:
    """
    Сервис для оформления и удаления подписки между пользователями
    """

    @classmethod
    async def create_follower(
            cls, current_user: User, following_user_id: int,
            session: AsyncSession
    ) -> None:
        """
        Создание подписки на пользователя по id
        :param current_user: объект текущего пользователя
        :param following_user_id: id пользователя для подписки
        :param session: объект асинхронной сессии
        :return: None
        """
        logger.debug(
            f"Запрос подписки пользователя id: {current_user.id} на id: {following_user_id} "
        )

        if await UserService.check_user_for_id(
                current_user_id=current_user.id, user_id=following_user_id
        ):
            logger.error(
                "Невалидные данные - попытка подписаться на самого себя")

            raise CustomApiException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Invalid data. You can't subscribe to yourself",
            )

        following_user = await UserService.get_user_for_id(
            user_id=following_user_id, session=session
        )

        if not following_user:
            logger.error(
                f"Не найден пользователь для подписки (id: {following_user_id})"
            )

            raise CustomApiException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="The subscription user was not found",
            )

        if await cls.check_follower(
                current_user=current_user, following_user_id=following_user.id
        ):
            logger.warning(f"Подписка уже оформлена")

            raise CustomApiException(
                status_code=HTTPStatus.LOCKED,
                detail="The user is already subscribed",
            )

        current_user_db = await UserService.get_user_for_id(
            user_id=current_user.id, session=session
        )

        current_user_db.following.append(following_user)
        await session.commit()

        logger.info(f"Подписка оформлена")

    @classmethod
    async def check_follower(cls, current_user: User,
                             following_user_id: int) -> bool:
        """
        Проверка наличия подписки
        :param current_user: объект текущего пользователя
        :param following_user_id: id пользователя для подписки
        :return: True - если текущий пользователь уже подписан | False - иначе
        """

        return following_user_id in [
            following.id for following in current_user.following
        ]

    @classmethod
    async def delete_follower(
            cls, current_user: User, followed_user_id: int,
            session: AsyncSession
    ) -> None:
        """
        Удаление подписки на пользователя
        :param current_user: объект текущего пользователя
        :param followed_user_id: id пользователя, от которого нужно отписаться
        :param session: объект асинхронной сессии
        :return: None
        """
        logger.debug(
            f"Запрос удаления подписки пользователя id: {current_user.id} от id: {followed_user_id}"
        )

        if await UserService.check_user_for_id(
                current_user_id=current_user.id, user_id=followed_user_id
        ):
            logger.error(
                "Невалидные данные - попытка отписаться от самого себя")

            raise CustomApiException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="Invalid data. You can't unsubscribe from yourself",
            )

        followed_user = await UserService.get_user_for_id(
            user_id=followed_user_id, session=session
        )

        if not followed_user:
            logger.error(
                f"Не найден пользователь для отмены подписки (id: {followed_user})"
            )

            raise CustomApiException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="The user to cancel the subscription was not found",
            )

        if not await cls.check_follower(
                current_user=current_user, following_user_id=followed_user.id
        ):
            logger.warning(f"Подписка не обнаружена")

            raise CustomApiException(
                status_code=HTTPStatus.LOCKED,
                detail="The user is not among the subscribers",
            )

        current_user_db = await UserService.get_user_for_id(
            user_id=current_user.id, session=session
        )

        current_user_db.following.remove(followed_user)
        await session.commit()

        logger.info(f"Подписка удалена")


class ImageService:
    """
    Сервис для сохранения изображений при добавлении нового твита
    """

    @classmethod
    async def save_image(cls, image: UploadFile, session: AsyncSession) -> int:
        """
        Сохранение изображения (без привязки к твиту)
        :param image: файл
        :param session: объект асинхронной сессии
        :return: id изображения
        """
        logger.debug("Сохранение изображения")

        path = await save_image(file=image)
        image_obj = Image(path_media=path)
        session.add(image_obj)
        await session.commit()

        return image_obj.id

    @classmethod
    async def update_images(
            cls, tweet_media_ids: List[int], tweet_id: int,
            session: AsyncSession
    ) -> None:
        """
        Обновление изображений (привязка к твиту)
        :param tweet_media_ids: список с id изображений
        :param tweet_id: id твита для привязки изображений
        :param session: объект асинхронной сессии
        :return: None
        """
        logger.debug(
            f"Обновление изображений по id: {tweet_media_ids}, tweet_id: {tweet_id}"
        )

        query = (
            update(Image).where(Image.id.in_(tweet_media_ids)).values(
                tweet_id=tweet_id)
        )
        await session.execute(query)

    @classmethod
    async def get_images(cls, tweet_id: int, session: AsyncSession) -> List[
        Image]:
        """
        Получить изображения твита.
        Используется при удалении твита для удаления всех его изображений из файловой системы.
        :param tweet_id: id твита
        :param session: объект асинхронной сессии
        :return: None
        """
        logger.debug(f"Поиск изображений твита")

        query = select(Image).filter(Image.tweet_id == tweet_id)
        images = await session.execute(query)

        return list(chain(*images.all()))

    @classmethod
    async def delete_images(cls, tweet_id: int, session: AsyncSession) -> None:
        """
        Удаление изображений твита
        :param tweet_id: id твита
        :param session: объект асинхронной сессии
        :return: None
        """
        logger.debug("Удаление изображений твита")

        images = await cls.get_images(tweet_id=tweet_id, session=session)

        if images:
            await delete_images(images=images)
        else:
            logger.warning("Изображения не найдены")


class TweetsService:
    """
    Сервис для добавления, удаления и вывода твитов
    """

    @classmethod
    async def get_tweets(cls, user: User, session: AsyncSession):
        """
        Вывод последних твитов подписанных пользователей
        :param user: объект текущего пользователя
        :param session: объект асинхронной сессии
        :return: список с твитами
        """
        logger.debug("Вывод твитов")

        query = (
            select(Tweet)
            .filter(Tweet.user_id.in_(user.id for user in user.following))
            .options(
                joinedload(Tweet.user),
                joinedload(Tweet.likes).subqueryload(Like.user),
                joinedload(Tweet.images),
            )
            .order_by(Tweet.created_at.desc())
        )

        result = await session.execute(query)
        tweets = result.unique().scalars().all()

        return tweets

    @classmethod
    async def get_tweet(cls, tweet_id: int,
                        session: AsyncSession) -> Tweet | None:
        """
        Возврат твита по переданному id
        :param tweet_id: id твита для поиска
        :param session: объект асинхронной сессии
        :return: объект твита
        """
        logger.debug(f"Поиск твита по id: {tweet_id}")

        query = select(Tweet).where(Tweet.id == tweet_id)
        tweet = await session.execute(query)

        return tweet.scalar_one_or_none()

    @classmethod
    async def create_tweet(
            cls, tweet: TweetInSchema, current_user: User,
            session: AsyncSession
    ) -> Tweet:
        """
        Создание нового твита
        :param tweet: данные для нового твита
        :param current_user: объект текущего пользователя
        :param session: объект асинхронной сессии
        :return: объект нового твита
        """
        logger.debug("Добавление нового твита")

        new_tweet = Tweet(tweet_data=tweet.tweet_data, user_id=current_user.id)

        session.add(new_tweet)
        await session.flush()

        tweet_media_ids = tweet.tweet_media_ids

        if tweet_media_ids and tweet_media_ids != []:
            await ImageService.update_images(
                tweet_media_ids=tweet_media_ids, tweet_id=new_tweet.id,
                session=session
            )

        await session.commit()

        return new_tweet

    @classmethod
    async def delete_tweet(
            cls, user: User, tweet_id: int, session: AsyncSession
    ) -> None:
        """
        Удаление твита
        :param user: объект текущего пользователя
        :param tweet_id: id удаляемого твита
        :param session: объект асинхронной сессии
        :return: None
        """
        logger.debug(f"Удаление твита")

        tweet = await cls.get_tweet(tweet_id=tweet_id, session=session)

        if not tweet:
            logger.error("Твит не найден")

            raise CustomApiException(
                status_code=HTTPStatus.NOT_FOUND, detail="Tweet not found"
            )

        else:
            if tweet.user_id != user.id:
                logger.error("Запрос на удаление чужого твита")

                raise CustomApiException(
                    status_code=HTTPStatus.LOCKED,
                    detail="The tweet that is being accessed is locked",
                )

            else:
                await ImageService.delete_images(tweet_id=tweet.id,
                                                 session=session)
                await session.delete(tweet)
                await session.commit()


class LikeService:
    """
    Сервис для проставления лайков и дизлайков твитам
    """

    @classmethod
    async def like(cls, tweet_id: int, user_id: int,
                   session: AsyncSession) -> None:
        """
        Лайк твита
        :param tweet_id: id твита для лайка
        :param user_id: id пользователя
        :param session: объект асинхронной сессии
        :return: None
        """
        logger.debug(f"Лайк твита №{tweet_id}")

        tweet = await TweetsService.get_tweet(tweet_id=tweet_id,
                                              session=session)

        if not tweet:
            logger.error("Твит не найден")

            raise CustomApiException(
                status_code=HTTPStatus.NOT_FOUND, detail="Tweet not found"
            )

        if await cls.check_like_tweet(
                tweet_id=tweet_id, user_id=user_id, session=session
        ):
            logger.warning("Пользователь уже ставил лайк твиту")

            raise CustomApiException(
                status_code=HTTPStatus.LOCKED,
                detail="The user has already liked this tweet",
            )

        like_record = Like(user_id=user_id, tweets_id=tweet.id)

        session.add(like_record)
        await session.commit()

    @classmethod
    async def check_like_tweet(
            cls, tweet_id: int, user_id: int, session: AsyncSession
    ) -> Like | None:
        """
        Проверка лайка (метод возвращает запись о лайке, проверяя тем самым, ставил ли пользователь лайк
        указанному твиту)
        :param tweet_id: id твита
        :param user_id: id пользователя
        :param session: объект асинхронной сессии
        """
        logger.debug("Поиск записи о лайке")

        query = select(Like).where(Like.user_id == user_id,
                                   Like.tweets_id == tweet_id)
        like = await session.execute(query)

        return like.scalar_one_or_none()

    @classmethod
    async def dislike(cls, tweet_id: int, user_id: int,
                      session: AsyncSession) -> None:
        """
        Удаление лайка
        :param tweet_id: id твита
        :param user_id: id пользователя
        :param session: объект асинхронной сессии
        :return: None
        """
        logger.debug(f"Дизлайк твита №{tweet_id}")

        tweet = await TweetsService.get_tweet(tweet_id=tweet_id,
                                              session=session)

        if not tweet:
            logger.error("Твит не найден")

            raise CustomApiException(
                status_code=HTTPStatus.NOT_FOUND, detail="Tweet not found"
            )

        like_record = await cls.check_like_tweet(
            tweet_id=tweet_id, user_id=user_id, session=session
        )

        if like_record is None:
            logger.warning("Запись о лайке не найдена")

            raise CustomApiException(
                status_code=HTTPStatus.LOCKED,
                detail="The user has not yet liked this tweet",
            )

        await session.delete(like_record)

        await session.commit()


class UserService:
    """
    Сервис для вывода данных о пользователе
    """

    @classmethod
    async def get_user_for_key(cls, token: str,
                               session: AsyncSession) -> User | None:
        """
        Возврат объекта пользователя по токену
        :param token: api-ключ пользователя
        :param session: объект асинхронной сессии
        :return: объект пользователя / False
        """
        logger.debug(f"Поиск пользователя по api-key: {token}")

        query = (
            select(User)
            .where(User.api_key == token)
            .options(selectinload(User.following),
                     selectinload(User.followers))
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @classmethod
    async def get_user_for_id(cls, user_id: int,
                              session: AsyncSession) -> User | None:
        """
        Возврат объекта пользователя по id
        :param user_id: id пользователя
        :param session: объект асинхронной сессии
        :return: объект пользователя / False
        """
        logger.debug(f"Поиск пользователя по id: {user_id}")

        query = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.following),
                     selectinload(User.followers))
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()

    @classmethod
    async def check_user_for_id(cls, current_user_id: int,
                                user_id: int) -> bool:
        """
        Проверка, является ли переданный id текущего пользователя.
        Используется при оформлении подписки пользователя, чтобы проверить, что пользователь не подписался сам на себя.
        :param current_user: объект текущего пользователя
        :param user_id: id пользователя для проверки
        :return: True - если переданный id == current_user.id | False - иначе
        """
        return current_user_id == user_id

    @classmethod
    async def check_users(cls) -> User | None:
        """
        Проверка наличия записей о пользователях в БД.
        Используется перед предварительным наполнением БД демонстрационными данными.
        :param session: объект асинхронной сессии
        :return: объект пользователя / False
        """
        async with async_session_maker() as session:
            logger.debug("Проверка данных о пользователях в БД")

            query = select(User)
            result = await session.execute(query)

            return result.scalars().all()
