import datetime
from sqlalchemy import ForeignKey, String, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from src.database import Base

user_to_user = Table(
    "user_to_user",
    Base.metadata,
    Column("followers_id",
           Integer,
           ForeignKey("users.id"),
           primary_key=True),
    Column("following_id",
           Integer,
           ForeignKey("users.id"),
           primary_key=True),
)


class Image(Base):
    """
    Модель для хранения данных об изображениях к твитам
    """

    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True,
                                    index=True)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id"),
                                          nullable=True)
    path_media: Mapped[str]

    __mapper_args__ = {"confirm_deleted_rows": False}


class Like(Base):
    """
    Модель для хранения данных о лайках к твитам
    """

    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True,
                                    index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tweets_id: Mapped[int] = mapped_column(ForeignKey("tweets.id"))

    __mapper_args__ = {"confirm_deleted_rows": False}


class Tweet(Base):
    """
    Модель для хранения твитов
    """

    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True,
                                    index=True)
    tweet_data: Mapped[str] = mapped_column(String(280))
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.utcnow, nullable=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    images: Mapped[List["Image"]] = relationship(
        backref="tweet", cascade="all, delete-orphan"
    )
    likes: Mapped[List["Like"]] = relationship(
        backref="tweet", cascade="all, delete-orphan"
    )

    __mapper_args__ = {"confirm_deleted_rows": False}


class User(Base):
    """
    Модель для хранения данных о пользователях
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True,
                                    index=True)
    username: Mapped[str] = mapped_column(
        String(60), nullable=False, unique=True, index=True
    )
    api_key: Mapped[str] = mapped_column()
    tweets: Mapped[List["Tweet"]] = relationship(
        backref="user", cascade="all, delete-orphan"
    )
    likes: Mapped[List["Like"]] = relationship(
        backref="user",
        cascade="all, delete-orphan",
    )

    following = relationship(
        "User",
        secondary=user_to_user,
        primaryjoin=id == user_to_user.c.followers_id,
        secondaryjoin=id == user_to_user.c.following_id,
        backref="followers",
        lazy="selectin",
    )

    __mapper_args__ = {"confirm_deleted_rows": False}
