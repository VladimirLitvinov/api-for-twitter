from typing import Optional
from http import HTTPStatus
from fastapi.security import APIKeyHeader
from starlette.requests import Request

from src.utils.exeptions import CustomApiException


class APITokenHeader(APIKeyHeader):
    """
    Проверка и извлечение токена из header
    """

    async def __call__(self, request: Request) -> Optional[str]:
        api_key = request.headers.get(self.model.name)

        if not api_key:
            if self.auto_error:
                raise CustomApiException(
                    status_code=HTTPStatus.UNAUTHORIZED,
                    detail="User authorization error",
                )
            else:
                return None

        return api_key


TOKEN = APITokenHeader(name="api-key")
