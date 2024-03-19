from fastapi import FastAPI

from src.routes.routes import user_router, image_router, tweet_router


def register_routers(app: FastAPI) -> FastAPI:
    """
    Регистрация роутов для API
    """

    app.include_router(user_router)
    app.include_router(image_router)
    app.include_router(tweet_router)

    return app
