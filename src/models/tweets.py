import datetime

from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String

from src.database import Base
from src.models.images import Image
from src.models.likes import Like


class Tweet(Base):
    """
    Модель для хранения твитов
    """

    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
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
