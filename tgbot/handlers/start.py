import logging
from random import randrange
from typing import List, Dict
import time
from loguru import logger

from aiogram import types
from aiogram.dispatcher import FSMContext

# Import modules of this project
from tgbot.loader import dp
from tgbot.utils.file_manager import get_text_from
from tgbot.services.business_logic import MarketBot, GameUser
from tgbot.handlers.new_user import new_gameuser_command
from tgbot.handlers.gameuser import send_gameuser_help


#  -------------------------------------------------------------- ВХОД ТГ ЮЗЕРА
def get_empty_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    return keyboard


@dp.message_handler(commands=['start'], state="*")
async def start_command(message: types.Message, state: FSMContext):
    logger.info('start command from: %r', message.from_user.id)

    MarketBot().add_tg_user(
        tg_id=message.from_user.id,
        tg_username=message.from_user.username
    )
    await message.answer(
        'Добро пожаловать!',
        reply_markup=types.ReplyKeyboardRemove())
    await new_gameuser_command(message, state)


@dp.message_handler(commands=['help'], state="*")
async def send_help(message: types.Message, state: FSMContext):
    logger.info('help command from: %r', message.from_user.id)
    gameuser_id = MarketBot().get_active_gameuser_id_for(message.from_user.id)
    await state.finish()
    if gameuser_id:
        gameuser = GameUser.get(gameuser_id)
        await send_gameuser_help(
            message=message,
            gameuser=gameuser
        )
    else:
        await message.answer(
            get_text_from('./tgbot/text_of_questions/help.txt'),
            reply_markup=get_empty_keyboard())
