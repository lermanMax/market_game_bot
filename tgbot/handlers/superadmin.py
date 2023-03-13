from random import randrange
from typing import List, Dict
import time
from loguru import logger

from aiogram import types
from aiogram.utils.exceptions import MessageNotModified
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Import modules of this project
from tgbot.loader import dp
from tgbot.config import SUPERADMIN_PASS, BOT_MAILADDRESS
from tgbot.keyboards.inline import make_inline_keyboard, button_cb
from tgbot.utils.file_manager import get_text_from
from tgbot.utils.broadcast import send_post, broadcast_post
from tgbot.utils.pars_messages import parse_message, Post
from tgbot.services.business_logic import Company, DealIllegal, Game, MarketBot, \
    NotEnoughMoney, SuperAdmin, GameUser, TgUser


#  ------------------------------------------------------ СОСТОЯНИЯ СУПЕРАДМИНА
class SuperAdminState(StatesGroup):
    waiting_for_pass = State()


async def superadmin_command_from_real_admin(message: types.Message):
    logger.info(
        'superadmin_command_from_real_admin from: %r',
        message.from_user.id)
    await message.answer(
        get_text_from('./tgbot/text_of_questions/admin.txt'))


@dp.message_handler(commands=['superadmin', 'sa'], state="*")
async def superadmin_command(message: types.Message):
    logger.info('superadmin_command from: %r', message.from_user.id)
    if message.from_user.id in MarketBot().get_superadmin_tg_ids():
        await superadmin_command_from_real_admin(message)
    else:
        await message.answer(
            "Вы пытаетесь войти в меню Суперадмина. Введите пароль:")
        MarketBot().add_tg_user(
            tg_id=message.from_user.id,
            tg_username=message.from_user.username
        )
        await SuperAdminState.waiting_for_pass.set()


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=SuperAdminState.waiting_for_pass)
async def check_superadmin_pass(message: types.Message, state: FSMContext):
    logger.info('check_superadmin_pass from: %r', message.from_user.id)
    if message.text == SUPERADMIN_PASS:
        await message.answer("Верный пароль")
        MarketBot().add_superadmin(message.from_user.id)
        await superadmin_command_from_real_admin(message)
        await state.finish()
    else:
        logger.warning('wrong_admin_pass from: %r', message.from_user.id)
        await message.answer("Неверный пароль. Попробуйте еще раз:")


#  -------------------------------------------------------------- СОЗДАНИЕ ИГРЫ
class NewGameState(StatesGroup):
    waiting_gs_link = State()


@dp.message_handler(commands=['new_game'], state="*")
async def new_game_command(message: types.Message, state: FSMContext):
    logger.info('new_game_command from: %r', message.from_user.id)
    if message.from_user.id not in MarketBot().get_superadmin_tg_ids():
        return
    await NewGameState.waiting_gs_link.set()
    game_id = SuperAdmin.create_new_game()
    await state.update_data(game_id=game_id)

    await message.answer(
        get_text_from('./tgbot/text_of_questions/new_game.txt'))
    await message.answer(
        f"Гугл аккаун бота: { BOT_MAILADDRESS }"
    )


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=NewGameState.waiting_gs_link)
async def new_gs_link(message: types.Message, state: FSMContext):
    logger.info('new_gs_link from: %r', message.from_user.id)

    if Game.is_url_correct(gs_url=message.text):
        state_data = await state.get_data()
        game = Game.get(state_data['game_id'])
        game.change_gslink(message.text)
        await state.finish()

        MarketBot().create_load_base_schedule(
            game=game,
            admin_id=message.from_user.id
        )

        logger.info('new_gs_link is correct')
        await message.answer(
            get_text_from('./tgbot/text_of_questions/gs_link_correct.txt')
        )
    else:
        logger.warning('new_gs_link is uncorrect')
        await message.reply(
            get_text_from('./tgbot/text_of_questions/gs_link_error.txt')
        )


#  ---------------------------------------------------------- УПРАВЛЕНИЕ ИГРАМИ
delete_button = 'Удалить'
stop_registration_button = 'Закрыть регистрацию'
open_registration_button = 'Открыть регистрацию'
stop_market_button = 'Закрыть торги'
open_market_button = 'Открыть торги'
stop_market_and_job_after_button = 'Закрыть торги и посчитать'
update_base_button = 'Обновить Базовые значения'


async def make_keyboard_for_game(game_id: int):
    keyboard = await make_inline_keyboard(
        question_name='game',
        answers=[
            open_registration_button,
            stop_registration_button,
            open_market_button,
            stop_market_button,
            stop_market_and_job_after_button,
            update_base_button,
        ],
        data=game_id
    )
    return keyboard

async def make_text_for_game(game: Game):
    text = (
        f'Игра: {game.game_id} {game.get_name()}\n'
        f'Ссылка: <a href="{game.get_gs_link()}">google sheet</a> \n'
        f'Регистрация: {game.is_registration_open()} \n'
        f'Торги: {game.is_market_open_now()} \n'
    )
    return text


@dp.message_handler(commands=['all_games'], state="*")
async def all_game_command(message: types.Message, state: FSMContext):
    logger.info('all_game_command from: %r', message.from_user.id)
    if message.from_user.id not in MarketBot().get_superadmin_tg_ids():
        return
    await message.answer('Все игры:')
    for game in MarketBot().get_games():
        keyboard = await make_keyboard_for_game(game.game_id)
        text = await make_text_for_game(game)
        await message.answer(
            text=text,
            reply_markup=keyboard
        )


async def delete_game(message: types.Message, game_id: int):
    logger.info('delete_game from: %r', message.from_user.id)


async def stop_registration_game(message: types.Message, game_id: int):
    logger.info('stop_registration_game from: %r', message.from_user.id)
    game = Game.get(game_id)
    game.close_registration()

    keyboard = await make_keyboard_for_game(game.game_id)
    text = await make_text_for_game(game)
    try:
        await message.edit_text(
            text=text,
            reply_markup=keyboard
        )
    except MessageNotModified:
        pass


async def open_registration_game(message: types.Message, game_id: int):
    logger.info('open_registration_game from: %r', message.from_user.id)
    game = Game.get(game_id)
    game.open_registration()

    keyboard = await make_keyboard_for_game(game.game_id)
    text = await make_text_for_game(game)
    try:
        await message.edit_text(
            text=text,
            reply_markup=keyboard
        )
    except MessageNotModified:
        pass


async def stop_market_game(message: types.Message, game_id: int):
    logger.info('stop_market_game from: %r', message.from_user.id)
    game = Game.get(game_id)
    game.close_market()

    keyboard = await make_keyboard_for_game(game.game_id)
    text = await make_text_for_game(game)
    try:
        await message.edit_text(
            text=text,
            reply_markup=keyboard
        )
    except MessageNotModified:
        pass


async def stop_market_and_job_after_game(message: types.Message, game_id: int):
    logger.info('stop_market_and_job_after_game from: %r', message.from_user.id)
    answer = await message.answer('Расчет запущен...')
    game = Game.get(game_id)
    game.job_after_close()

    keyboard = await make_keyboard_for_game(game.game_id)
    text = await make_text_for_game(game)
    await answer.delete()
    try:
        await message.edit_text(
            text=text,
            reply_markup=keyboard
        )
    except MessageNotModified:
        pass
    


async def open_market_game(message: types.Message, game_id: int):
    logger.info('open_market_game from: %r', message.from_user.id)
    game = Game.get(game_id)
    game.open_market()

    keyboard = await make_keyboard_for_game(game.game_id)
    text = await make_text_for_game(game)
    try:
        await message.edit_text(
            text=text,
            reply_markup=keyboard
        )
    except MessageNotModified:
        pass

async def update_base_game(message: types.Message, game_id: int):
    logger.info('update_base_game from: %r', message.from_user.id)
    answer = await message.answer('Начинаю обновление ...')
    game: Game = Game.get(game_id)
    result_loading = game.load_base_value()

    await answer.delete()
    if result_loading:
        text = f'База игры {game.game_id} успешно обновлена'
    else:
        text = f'Базу игры {game.game_id} не удалось обновить'
    await message.answer(text)


gameadmin_button_dict = {
    delete_button: delete_game,
    stop_registration_button: stop_registration_game,
    open_registration_button: open_registration_game,
    stop_market_button: stop_market_game,
    open_market_button: open_market_game,
    stop_market_and_job_after_button: stop_market_and_job_after_game,
    update_base_button: update_base_game,
}


@dp.callback_query_handler(
    button_cb.filter(question_name=['game']),
    state='*')
async def superadmin_buttons(
        query: types.CallbackQuery,
        callback_data: Dict[str, str],
        state: FSMContext):
    logger.info('Got this callback data: %r', callback_data)
    if query.from_user.id not in MarketBot().get_superadmin_tg_ids():
        return

    await gameadmin_button_dict[callback_data['answer']](
        message=query.message,
        game_id=callback_data['data']
    )


#  -------------------------------------------------------- УПРАВЛЕНИЕ ЮЗЕРАМИ
@dp.message_handler(commands=['ban', 'justify'], state="*")
async def ban_command(message: types.Message, state: FSMContext):
    logger.info('ban_command from: %r', message.from_user.id)
    if message.from_user.id not in MarketBot().get_superadmin_tg_ids():
        return

    words_command: List[str] = message.text.split(' ')
    if len(words_command) > 2 or not words_command[-1].isdigit():
        logger.info('bad command: %r', message.from_user.id)
        await message.reply('не верная команда')
        return

    command, tg_id = words_command
    try:
        user = TgUser.get(int(tg_id))
    except Exception:
        await message.reply('id не найден')
        return

    if command == '/ban':
        user.ban()
        await message.reply('забанено')
    elif command == '/justify':
        user.unban()
        await message.reply('разбанено')


#  -------------------------------------------------------- РАССЫЛКА СООБЩЕНИЙ
class Mailing(StatesGroup):
    WaitLetter = State()

mailing_cb = CallbackData('mailing_cb', 'target')

@dp.message_handler(commands=['mailing'], state='*')
async def letter_for_mailing_handler(message: types.Message):
    logger.info(f'letter_for_mailing_handler from: { message.from_user.id}',)
    if message.from_user.id not in MarketBot().get_superadmin_tg_ids():
        return
    text = 'Напишите сообщение. Потом можно будет выбрать кому его отправить.'
    await Mailing.WaitLetter.set()
    await message.answer(text=text)


@dp.message_handler(
        content_types=types.message.ContentType.ANY,
        state=Mailing.WaitLetter)
async def start_mailing_handler(message: types.Message, state: FSMContext):
    logger.info(f'start_mailing_handler from: {message.from_user.id}')
    
    parsed_post: Post = await parse_message(message)

    await state.reset_state()
    # make keyboard with game ids
    inline_buttons = []
    inline_buttons.append(
            [
                InlineKeyboardButton(
                    text='Удалить',
                    callback_data=mailing_cb.new(target='delete')),
            ]
        )
    for game in MarketBot().get_games():
        inline_buttons.append(
            [
                InlineKeyboardButton(
                    text=f'Игра {game.game_id}',
                    callback_data=mailing_cb.new(target=str(game.game_id))
                ),
            ]
        )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=inline_buttons
    )
    await broadcast_post(parsed_post, message.from_user.id, reply_markup=keyboard)


@dp.callback_query_handler(mailing_cb.filter())
async def mailing_broadcast_handler(call: types.CallbackQuery, callback_data: Dict[str, str]):
    target = str(callback_data['target'])
    if target=='delete':
        await call.message.delete()
        await call.message.answer('Удалено')
        return
    await call.message.edit_reply_markup(InlineKeyboardMarkup())

    game: Game = Game.get(int(target))
    users_id = game.get_gameuser_tg_ids()
    result_text = await broadcast_post(
        post=await parse_message(call.message),
        users_id=users_id,
        show_result=True
    )
    await call.message.answer(result_text)
