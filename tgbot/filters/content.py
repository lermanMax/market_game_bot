from aiogram import types
from aiogram.dispatcher.filters import Filter
from aiogram.dispatcher.handler import ctx_data
from aiogram.types.message import ContentType

from tgbot.loader import bot


class TextNotComand(Filter):

    async def check(self, message: types.Message, *args, **kwargs) -> bool:
        if message.content_type == ContentType.TEXT:
            if not message.text.startswith('/'):
                return True

        return False