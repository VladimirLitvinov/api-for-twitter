from typing import Annotated
from http import HTTPStatus
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.models.models import User
from src.database import get_async_session
from src.schemas.schemas import UserOutSchema, ImageResponseSchema, \
    TweetResponseSchema, TweetInSchema, TweetListSchema
from src.services.services import FollowerService, ImageService, LikeService, \
    TweetsService, UserService
from src.utils.exeptions import CustomApiException
from src.utils.user import get_current_user

from src.schemas.base_response import (
    ResponseSchema,
    UnauthorizedResponseSchema,
    ValidationResponseSchema,
    LockedResponseSchema,
    ErrorResponseSchema,
    BadResponseSchema
)

image_router = APIRouter(
    prefix="/api/medias", tags=["medias"]
)
tweet_router = APIRouter(
    prefix="/api/tweets", tags=["tweets"]
)

user_router = APIRouter(
    prefix="/api/users", tags=["users"]
)


@image_router.post(
    "",
    response_model=ImageResponseSchema,
    responses={
        401: {"model": UnauthorizedResponseSchema},
        400: {"model": BadResponseSchema},
        422: {"model": ValidationResponseSchema},
    },
    status_code=201,
)
async def add_image(
        file: UploadFile,
        session: AsyncSession = Depends(get_async_session),
):
    """
    Загрузка изображения к твиту
    """
    if not file:
        logger.error("Изображение не передано в запросе")

        raise CustomApiException(
            status_code=HTTPStatus.BAD_REQUEST,  # 400
            detail="The image was not attached to the request",
        )

    image_id = await ImageService.save_image(image=file, session=session)

    return {"media_id": image_id}


@tweet_router.get(
    "",
    response_model=TweetListSchema,
    responses={401: {"model": UnauthorizedResponseSchema}},
    status_code=200,
)
async def get_tweets(
        current_user: Annotated[User, Depends(get_current_user)],
        session: AsyncSession = Depends(get_async_session),
):
    """
    Вывод ленты твитов (выводятся твиты людей,
     на которых подписан пользователь)
    """
    tweets = await TweetsService.get_tweets(user=current_user, session=session)

    return {"tweets": tweets}


@tweet_router.post(
    "",
    response_model=TweetResponseSchema,
    responses={
        401: {"model": UnauthorizedResponseSchema},
        422: {"model": ValidationResponseSchema},
    },
    status_code=201,
)
async def create_tweet(
        tweet: TweetInSchema,
        current_user: Annotated[User, Depends(get_current_user)],
        session: AsyncSession = Depends(get_async_session),
):
    """
    Добавление твита
    """
    tweet = await TweetsService.create_tweet(
        tweet=tweet, current_user=current_user, session=session
    )

    return {"tweet_id": tweet.id}


@tweet_router.delete(
    "/{tweet_id}",
    response_model=ResponseSchema,
    responses={
        401: {"model": UnauthorizedResponseSchema},
        404: {"model": ErrorResponseSchema},
        422: {"model": ValidationResponseSchema},
        423: {"model": LockedResponseSchema},
    },
    status_code=200,
)
async def delete_tweet(
        tweet_id: int,
        current_user: Annotated[User, Depends(get_current_user)],
        session: AsyncSession = Depends(get_async_session),
):
    """
    Удаление твита
    """
    await TweetsService.delete_tweet(
        user=current_user, tweet_id=tweet_id, session=session
    )

    return {"result": True}


@tweet_router.post(
    "/{tweet_id}/likes",
    response_model=ResponseSchema,
    responses={
        401: {"model": UnauthorizedResponseSchema},
        404: {"model": ErrorResponseSchema},
        422: {"model": ValidationResponseSchema},
        423: {"model": LockedResponseSchema},
    },
    status_code=201,
)
async def create_like(
        tweet_id: int,
        current_user: Annotated[User, Depends(get_current_user)],
        session: AsyncSession = Depends(get_async_session),
):
    """
    Лайк твита
    """
    await LikeService.like(tweet_id=tweet_id, user_id=current_user.id,
                           session=session)

    return {"result": True}


@tweet_router.delete(
    "/{tweet_id}/likes",
    response_model=ResponseSchema,
    responses={
        401: {"model": UnauthorizedResponseSchema},
        404: {"model": ErrorResponseSchema},
        422: {"model": ValidationResponseSchema},
        423: {"model": LockedResponseSchema},
    },
    status_code=200,
)
async def delete_like(
        tweet_id: int,
        current_user: Annotated[User, Depends(get_current_user)],
        session: AsyncSession = Depends(get_async_session),
):
    """
    Удаление лайка
    """
    await LikeService.dislike(
        tweet_id=tweet_id, user_id=current_user.id, session=session
    )

    return {"result": True}


@user_router.get(
    "/me",
    response_model=UserOutSchema,
    responses={401: {"model": UnauthorizedResponseSchema}},
    status_code=200,
)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """
    Вывод данных о текущем пользователе: id, username, подписки, подписчики
    """
    return {"user": current_user}


@user_router.post(
    "/{user_id}/follow",
    response_model=ResponseSchema,
    responses={
        401: {"model": UnauthorizedResponseSchema},
        404: {"model": ErrorResponseSchema},
        422: {"model": ValidationResponseSchema},
        423: {"model": LockedResponseSchema},
    },
    status_code=201,
)
async def create_follower(
        user_id: int,
        current_user: Annotated[User, Depends(get_current_user)],
        session: AsyncSession = Depends(get_async_session),
):
    """
    Подписка на пользователя
    """
    await FollowerService.create_follower(
        current_user=current_user, following_user_id=user_id, session=session
    )

    return {"result": True}


@user_router.delete(
    "/{user_id}/follow",
    response_model=ResponseSchema,
    responses={
        401: {"model": UnauthorizedResponseSchema},
        404: {"model": ErrorResponseSchema},
        422: {"model": ValidationResponseSchema},
        423: {"model": LockedResponseSchema},
    },
    status_code=200,
)
async def delete_follower(
        user_id: int,
        current_user: Annotated[User, Depends(get_current_user)],
        session: AsyncSession = Depends(get_async_session),
):
    """
    Отписка от пользователя
    """
    await FollowerService.delete_follower(
        current_user=current_user, followed_user_id=user_id, session=session
    )

    return {"result": True}


@user_router.get(
    "/{user_id}",
    response_model=UserOutSchema,
    responses={
        401: {"model": UnauthorizedResponseSchema},
        404: {"model": ErrorResponseSchema},
        422: {"model": ValidationResponseSchema},
        423: {"model": LockedResponseSchema},
    },
    status_code=200,
)
async def get_user(user_id: int,
                   session: AsyncSession = Depends(get_async_session)):
    """
    Вывод данных о пользователе: id, username, подписки, подписчики
    """
    user = await UserService.get_user_for_id(user_id=user_id, session=session)

    if user is None:
        raise CustomApiException(
            status_code=HTTPStatus.NOT_FOUND, detail="User not found"
        )

    return {"user": user}
