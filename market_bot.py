import asyncio
import logging
import typing

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import callback_data, exceptions
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Import modules of this project
from config import API_TOKEN, SUPERADMIN_PASS, BOT_MAILADDRESS
from business_logic import Game, MarketBot, SuperAdmin, TgUser

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('messages_sender')

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# Sructure of callback buttons
button_cb = callback_data.CallbackData(
    'B', 'q_name', 'ans', 's_id', 'data')

# Initialize business logic
market_bot = MarketBot()


def get_text_from(path):
    with open(path, 'r') as file:
        one_string = ''
        for line in file.readlines():
            one_string += line
    return one_string


#  ------------------------------------------------------ ВХОД ТГ ЮЗЕРА
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    logging.info('start command from: %r', message.from_user.id)

    market_bot.add_tg_user(
        tg_id=message.from_user.id,
        tg_username=message.from_user.username
    )
    await message.answer(
        get_text_from('./text_of_questions/instruction.txt'))

    await message.answer(
        get_text_from('./text_of_questions/game_entry.txt'))


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    logging.info('help command from: %r', message.from_user.id)
    await message.answer(
        get_text_from('./text_of_questions/help.txt'))


#  ------------------------------------------------------ СОСТОЯНИЯ СУПЕРАДМИНА
class SuperAdminState(StatesGroup):
    waiting_for_pass = State()
    real_admin = State()


async def superadmin_command_from_real_admin(message: types.Message):
    logging.info(
        'superadmin_command_from_real_admin from: %r',
        message.from_user.id)
    await message.answer(
        get_text_from('./text_of_questions/admin.txt'))


@dp.message_handler(commands=['superadmin'], state="*")
async def superadmin_command(message: types.Message):
    logging.info('superadmin_command from: %r', message.from_user.id)
    if message.from_user.id in market_bot.get_superadmin_tg_ids():
        await superadmin_command_from_real_admin(message)
    else:
        await message.answer(
            "Вы пытаетесь войти в меню Суперадмина. Введите пароль:")
        await SuperAdminState.waiting_for_pass.set()


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=SuperAdminState.waiting_for_pass
)
async def check_superadmin_pass(message: types.Message, state: FSMContext):
    logging.info('check_superadmin_pass from: %r', message.from_user.id)
    if message.text == SUPERADMIN_PASS:
        await message.answer("Верный пароль")
        market_bot.add_superadmin(message.from_user.id)
        await superadmin_command_from_real_admin(message)
        await SuperAdminState.next()
    else:
        await message.answer("Неверный пароль. Попробуйте еще раз:")


#  -------------------------------------------------------------- СОЗДАНИЕ ИГРЫ
class NewGameState(StatesGroup):
    waiting_gs_link = State()


@dp.message_handler(commands=['new_game'], state="*")
async def new_game_command(message: types.Message, state: FSMContext):
    logging.info('new_game_command from: %r', message.from_user.id)
    if message.from_user.id not in market_bot.get_superadmin_tg_ids():
        return

    await NewGameState.waiting_gs_link.set()
    game_id = SuperAdmin.create_new_game()
    print(game_id)
    await state.update_data(game_id=game_id)

    await message.answer(
        get_text_from('./text_of_questions/new_game.txt'))
    await message.answer(
        f"Гугл аккаун бота: { BOT_MAILADDRESS }"
    )


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=NewGameState.waiting_gs_link
)
async def new_gs_link(message: types.Message, state: FSMContext):
    logging.info('new_gs_link from: %r', message.from_user.id)

    if Game.is_url_correct(message.text):
        game = await Game(state['game_id'])
        await game.change_gslink(message.text)
        await NewGameState.next()
        await message.answer("Проблемы с этой ссылкой. Попробуйте еще раз:")
    else:
        await message.reply("Проблемы с этой ссылкой. Попробуйте еще раз:")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
