from http import HTTPStatus
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, model_validator, field_validator
from pydantic import Field

from src.schemas.base_response import ResponseSchema
from src.utils.exeptions import CustomApiException


class ImageResponseSchema(ResponseSchema):
    """
    Схема для вывода id изображения после публикации твита
    """

    id: int = Field(alias="media_id")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class ImagePathSchema(BaseModel):
    """
    Схема для вывода ссылки на изображения при отображении твитов
    """

    path_media: str

    model_config = ConfigDict(from_attributes=True)


class LikeSchema(BaseModel):
    """
    Схема для вывода лайков при выводе твитов
    """

    id: int = Field(alias="user_id")
    username: str = Field(alias="name")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @model_validator(mode="before")
    def extract_user(cls, data):
        """
        Метод извлекает и возвращает данные о пользователе из объекта Like
        """

        user = data.user
        return user


class UserSchema(BaseModel):
    """
    Базовая схема для вывода основных данных о пользователе
    """

    id: int
    username: str = Field(alias="name")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class UserDataSchema(UserSchema):
    """
    Схема для вывода детальной информации о пользователе
    """

    following: Optional[List["UserSchema"]] = []
    followers: Optional[List["UserSchema"]] = []

    model_config = ConfigDict(from_attributes=True)


class UserOutSchema(ResponseSchema):
    """
    Схема для вывода ответа с детальными данными о пользователе
    """

    user: UserDataSchema


class TweetInSchema(BaseModel):
    """
    Схема для входных данных при добавлении нового твита
    """

    tweet_data: str = Field()
    tweet_media_ids: Optional[list[int]]

    @field_validator("tweet_data", mode="before")
    @classmethod
    def check_len_tweet_data(cls, val: str) -> str | None:
        """
        Проверка длины твита с переопределением вывода ошибки в случае превышения
        """
        if len(val) > 280:
            raise CustomApiException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,  # 422
                detail=f"The length of the "
                       f"tweet should not exceed 280 characters. "
                       f"Current value: {len(val)}",
            )

        return val

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TweetResponseSchema(ResponseSchema):
    """
    Схема для вывода id твита после публикации
    """

    id: int = Field(alias="tweet_id")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TweetOutSchema(BaseModel):
    """
    Схема для вывода твита, автора, вложенных изображений и данных по лайкам
    """

    id: int
    tweet_data: str = Field(alias="content")
    user: UserSchema = Field(alias="author")
    likes: List[LikeSchema]
    images: List[str] = Field(alias="attachments")

    @field_validator("images", mode="before")
    def serialize_images(cls, val: List[ImagePathSchema]):
        """
        Возвращаем список строк с ссылками на изображение
        """
        if isinstance(val, list):
            return [v.path_media for v in val]

        return val

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TweetListSchema(ResponseSchema):
    """
    Схема для вывода списка твитов
    """

    tweets: List[TweetOutSchema]
