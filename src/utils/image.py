import os
import aiofiles

from typing import List
from http import HTTPStatus
from contextlib import suppress
from datetime import datetime
from fastapi import UploadFile
from loguru import logger

from src.config import ALLOWED_EXTENSIONS, IMAGES_FOLDER
from src.models.models import Image
from src.utils.exeptions import CustomApiException


def allowed_image(image_name: str) -> None:
    """
    Проверка расширения изображения
    :param image_name: название изображения
    :return: None
    """
    logger.debug("Проверка формата изображения")

    if "." in image_name and image_name.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS:
        logger.info("Формат изображения корректный")
    else:
        logger.error("Неразрешенный формат изображения")

        raise CustomApiException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"The image has an unresolved format. You can only download the following formats: "
            f"{', '.join(ALLOWED_EXTENSIONS)}",
        )


def clear_path(path: str) -> str:
    """
    Очистка входной строки от "static"
    :param path: строка - полный путь
    :return: очищенная строка
    """
    return path.split("static")[1][1:]


async def create_directory(path: str) -> None:
    """
    Создаем папку для сохранения изображений
    """
    logger.debug(f"Создание директории: {path}")
    os.makedirs(path)


async def save_image(file: UploadFile, avatar=False) -> str:
    """
    Сохранение изображения
    :param avatar: переключатель для сохранения аватара пользователя или изображения к твиту
    :param image: файл - изображение
    :return: путь относительно static для сохранения в БД
    """
    allowed_image(image_name=file.filename)

    with suppress(OSError):
        if avatar:
            logger.debug("Сохранение аватара пользователя")
            path = os.path.join(IMAGES_FOLDER, "avatars")

        else:
            logger.debug("Сохранение изображения к твиту")
            current_date = datetime.now()
            path = os.path.join(
                IMAGES_FOLDER,
                "tweets",
                f"{current_date.year}",
                f"{current_date.month}",
                f"{current_date.day}",
            )

        if not os.path.isdir(path):
            await create_directory(path=path)

        contents = file.file.read()
        full_path = os.path.join(path, f"{file.filename}")

        async with aiofiles.open(full_path, mode="wb") as f:
            await f.write(contents)

        return clear_path(path=full_path)


async def delete_images(images: List[Image]) -> None:
    """
    Удаление из файловой системы изображений
    :param images: объекты изображений из БД
    :return: None
    """
    logger.debug(f"Удаление изображений из файловой системы")

    folder = os.path.join(
        "static", images[0].path_media.rsplit("/", 1)[0].rsplit("\\", 1)[0]
    )

    for img in images:
        try:
            os.remove(os.path.join("static", img.path_media))
            logger.debug(f"Изображение №{img.id} - {img.path_media} удалено")

        except FileNotFoundError:
            logger.error(f"Директория: {img.path_media} не найдена")

    logger.info("Все изображения удалены")

    await check_and_delete_folder(path=folder)


async def check_and_delete_folder(path: str) -> None:
    """
    Проверка и удаление папки, если пуста (подчистка пустых директорий после удаления твитов с изображениями)
    :param path: директория с изображениями после удаления твита
    :return: None
    """
    try:
        if len(os.listdir(path)) == 0:
            os.rmdir(path)
            logger.info(f"Директория: {path} удалена")

    except FileNotFoundError:
        logger.error(f"Директория: {path} не найдена")
