from fastapi import FastAPI

from src.routes.user import router as user_router
from src.routes.image import router as media_router
from src.routes.tweet import router as tweet_router


def register_routers(app: FastAPI) -> FastAPI:
    """
    Регистрация роутов для API
    """

    app.include_router(user_router)
    app.include_router(media_router)
    app.include_router(tweet_router)

    return app
