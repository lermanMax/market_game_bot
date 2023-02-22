from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from loguru import logger

from tgbot.services.business_logic import TgUser


class AccessMiddleware(BaseMiddleware):

    async def on_pre_process_message(
            self, message: types.Message, data: dict, *arg, **kwargs):
        user_from_tg = types.User.get_current()
        tg_id = user_from_tg.id
        logger.info(f'user_from_tg: {tg_id}')
        if TgUser.get(tg_id):
            if TgUser.get(tg_id).is_blocked():
                logger.info(f'Пользователь {tg_id} заблокирован')
                return CancelHandler()
