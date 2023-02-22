from aiogram import types
from aiogram.dispatcher.filters import Filter

from tgbot.config import TG_ADMINS_ID


class IsAdminUserFilter(Filter):

    async def check(self, message: types.Message, *args, **kwargs) -> bool:
        return bool(message.from_user.id in TG_ADMINS_ID)
