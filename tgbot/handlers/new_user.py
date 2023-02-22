from random import randrange
from typing import List, Dict
import time
from loguru import logger

from aiogram import Bot, Dispatcher, executor, types

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Import modules of this project
from tgbot.loader import dp
from keyboards.gameuser import gameuser_keyboard
from tgbot.utils.file_manager import get_text_from
from tgbot.services.business_logic import Company, DealIllegal, Game, MarketBot, \
    NotEnoughMoney, SuperAdmin, GameUser, TgUser


#  ------------------------------------------------------------ СОЗДАНИЕ ИГРОКА
class NewGameUser(StatesGroup):
    waiting_game_key = State()
    waiting_last_name = State()
    waiting_first_name = State()
    waiting_nickname = State()


@dp.message_handler(commands=['new_user'], state="*")
async def new_gameuser_command(message: types.Message, state: FSMContext):
    logger.info('new_gameuser_command from: %r', message.from_user.id)

    await NewGameUser.waiting_game_key.set()
    await message.answer(
        get_text_from('./tgbot/text_of_questions/game_entry.txt'))


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=NewGameUser.waiting_game_key)
async def gameuser_gamekey(message: types.Message, state: FSMContext):
    logger.info('gameuser_gamekey from: %r', message.from_user.id)
    game = MarketBot().get_game_by_game_key(
        game_key=message.text
    )

    if not game:
        logger.warning('wrong gamekey from: %r', message.from_user.id)
        await message.answer(
            get_text_from('./tgbot/text_of_questions/game_key_wrong.txt'))
        return

    if not game.is_registration_open():
        logger.warning(f'registration closed: {game.game_id}')
        await message.answer(
            get_text_from('./tgbot/text_of_questions/registration_closed.txt'))
        return

    if game.gameuser_in_game(tg_id=message.from_user.id):
        logger.info('gameuser already exist: %r', message.from_user.id)
        await state.finish()
        await message.answer(
            get_text_from('./tgbot/text_of_questions/gameuser_in_game.txt'))
    else:
        gameuser = game.add_gameuser(tg_id=message.from_user.id)
        gameuser.activate()
        await NewGameUser.next()
        await message.answer(
                get_text_from('./tgbot/text_of_questions/game_key_correct.txt'))


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=NewGameUser.waiting_last_name)
async def gameuser_lastname(message: types.Message, state: FSMContext):
    logger.info('gameuser_lastname from: %r', message.from_user.id)

    gameuser_id = MarketBot().get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    gameuser.change_last_name(
        new_last_name=message.text
    )
    await NewGameUser.next()
    await message.answer(
            get_text_from('./tgbot/text_of_questions/last_name_correct.txt'))


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=NewGameUser.waiting_first_name)
async def gameuser_firstname(message: types.Message, state: FSMContext):
    logger.info('gameuser_firstname from: %r', message.from_user.id)

    gameuser_id = MarketBot().get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    gameuser.change_first_name(
        new_first_name=message.text
    )
    await NewGameUser.next()
    await message.answer(
            get_text_from('./tgbot/text_of_questions/first_name_correct.txt'))


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=NewGameUser.waiting_nickname)
async def gameuser_nickname(message: types.Message, state: FSMContext):
    logger.info('gameuser_nickname from: %r', message.from_user.id)

    gameuser_id = MarketBot().get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    if gameuser.is_nickname_unique(nickname=message.text):
        gameuser.change_nickname(
            new_nickname=message.text
        )
        await state.finish()
        text = (
            f'{gameuser.get_first_name()}, я успешно зарегистрировал '
            f'тебя в игре {gameuser.get_game().game_id} '
            f'под ником {gameuser.get_nickname()}'
        )
        await message.answer(
            text,
            reply_markup=gameuser_keyboard
        )
        game = gameuser.get_game()
        game.add_gameuser_in_sheet(gameuser_id)
        await start_guide(message)
    else:
        logger.info('wrong gameuser_nickname from: %r', message.from_user.id)
        await message.answer(
            get_text_from('./tgbot/text_of_questions/nickname_wrong.txt'))


async def start_guide(message: types.Message):
    logger.info('start_guide from: %r', message.from_user.id)
    await message.answer(
            get_text_from('./tgbot/text_of_questions/about_1.txt'))
    time.sleep(3)
    await message.answer(
            get_text_from('./tgbot/text_of_questions/about_2.txt'))
    time.sleep(3)
    await message.answer(
            get_text_from('./tgbot/text_of_questions/about_3.txt'))