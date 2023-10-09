from loguru import logger
from typing import Dict, List
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.types.message import ContentType

from tgbot.loader import dp


@dp.message_handler(commands=['id'], state='*')
async def id_handler(message: Message, state: FSMContext,):
    await state.reset_state()
    text = f'Ваш ID: <code>{message.from_user.id}</code>\n'
    if message.from_user.id != message.chat.id:
        text += f'Ваш чат: <code>{message.chat.id}</code>'
    await message.answer(text)


@dp.message_handler(content_types=ContentType.TEXT, state='*')
async def text_handler(message: Message):
    logger.info(f'chat:{message.chat.id} Text: {message.text[:20]}')


@dp.message_handler(content_types=ContentType.PHOTO, state='*')
async def photo_handler(message: Message):
    logger.info(f'chat:{message.chat.id} Photo: {message.photo[0].file_id}')

@dp.callback_query_handler()
async def someshite_handler(call: CallbackQuery, callback_data: Dict[str, str]):
    logger(f'someshite_handler from: {call.from_user.id} callback {callback_data}')