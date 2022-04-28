import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import callback_data
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Import modules of this project
from config import API_TOKEN, SUPERADMIN_PASS, BOT_MAILADDRESS
from schedule_module import schedule, run_continuously
from business_logic import Game, MarketBot, SuperAdmin, GameUser

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('market_bot')

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# Sructure of callback buttons
button_cb = callback_data.CallbackData(
    'B', 'q_name', 'ans', 's_id', 'data')

# Start the background thread of schedule
stop_run_continuously = run_continuously(interval=20)
waiting_key_games = {}

# Initialize business logic
market_bot = MarketBot()


def get_text_from(path):
    with open(path, 'r') as file:
        one_string = ''
        for line in file.readlines():
            one_string += line
    return one_string


#  -------------------------------------------------------------- ВХОД ТГ ЮЗЕРА
def get_empty_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    return keyboard


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message, state: FSMContext):
    log.info('start command from: %r', message.from_user.id)

    market_bot.add_tg_user(
        tg_id=message.from_user.id,
        tg_username=message.from_user.username
    )
    await message.answer(
        get_text_from('./text_of_questions/instruction.txt'),
        reply_markup=get_empty_keyboard())
    await new_gameuser_command(message, state)


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    log.info('help command from: %r', message.from_user.id)
    gameuser_id = market_bot.get_active_gameuser_id_for(message.from_user.id)
    if gameuser_id:
        await message.answer(
            get_text_from('./text_of_questions/help.txt'),
            reply_markup=get_gameuser_keyboard())
    else:
        await message.answer(
            get_text_from('./text_of_questions/help.txt'),
            reply_markup=get_empty_keyboard())


#  ------------------------------------------------------ СОСТОЯНИЯ СУПЕРАДМИНА
class SuperAdminState(StatesGroup):
    waiting_for_pass = State()


async def superadmin_command_from_real_admin(message: types.Message):
    log.info(
        'superadmin_command_from_real_admin from: %r',
        message.from_user.id)
    await message.answer(
        get_text_from('./text_of_questions/admin.txt'))


@dp.message_handler(commands=['superadmin'], state="*")
async def superadmin_command(message: types.Message):
    log.info('superadmin_command from: %r', message.from_user.id)
    if message.from_user.id in market_bot.get_superadmin_tg_ids():
        await superadmin_command_from_real_admin(message)
    else:
        await message.answer(
            "Вы пытаетесь войти в меню Суперадмина. Введите пароль:")
        await SuperAdminState.waiting_for_pass.set()


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=SuperAdminState.waiting_for_pass)
async def check_superadmin_pass(message: types.Message, state: FSMContext):
    log.info('check_superadmin_pass from: %r', message.from_user.id)
    if message.text == SUPERADMIN_PASS:
        await message.answer("Верный пароль")
        market_bot.add_superadmin(message.from_user.id)
        await superadmin_command_from_real_admin(message)
        await state.finish()
    else:
        log.warning('wrong_admin_pass from: %r', message.from_user.id)
        await message.answer("Неверный пароль. Попробуйте еще раз:")


#  -------------------------------------------------------------- СОЗДАНИЕ ИГРЫ
class NewGameState(StatesGroup):
    waiting_gs_link = State()


@dp.message_handler(commands=['new_game'], state="*")
async def new_game_command(message: types.Message, state: FSMContext):
    log.info('new_game_command from: %r', message.from_user.id)
    if message.from_user.id not in market_bot.get_superadmin_tg_ids():
        return
    await NewGameState.waiting_gs_link.set()
    game_id = SuperAdmin.create_new_game()
    await state.update_data(game_id=game_id)

    await message.answer(
        get_text_from('./text_of_questions/new_game.txt'))
    await message.answer(
        f"Гугл аккаун бота: { BOT_MAILADDRESS }"
    )


def load_base_value_if_its_ready(game: Game, admin_id: int):
    def job():
        if game.load_base_value_if_its_ready():
            log.info(f'base values soccesful loaded in game: { game.game_id }')
            game.open_market()
            return schedule.CancelJob
    return job


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=NewGameState.waiting_gs_link)
async def new_gs_link(message: types.Message, state: FSMContext):
    log.info('new_gs_link from: %r', message.from_user.id)

    if Game.is_url_correct(gs_url=message.text):
        state_data = await state.get_data()
        game = Game.get(state_data['game_id'])
        game.change_gslink(message.text)
        await state.finish()
        schedule.every(10).seconds.do(
            load_base_value_if_its_ready(
                game=game,
                admin_id=message.from_user.id
            )
        )
        log.info('new_gs_link is correct')
        await message.answer(
            get_text_from('./text_of_questions/gs_link_correct.txt')
        )
    else:
        log.warning('new_gs_link is uncorrect')
        await message.reply(
            get_text_from('./text_of_questions/gs_link_error.txt')
        )


#  ------------------------------------------------------------ СОЗДАНИЕ ИГРОКА
class NewGameUser(StatesGroup):
    waiting_game_key = State()
    waiting_last_name = State()
    waiting_first_name = State()
    waiting_nickname = State()


@dp.message_handler(commands=['new_user'], state="*")
async def new_gameuser_command(message: types.Message, state: FSMContext):
    log.info('new_gameuser_command from: %r', message.from_user.id)

    await NewGameUser.waiting_game_key.set()
    await message.answer(
        get_text_from('./text_of_questions/game_entry.txt'))


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=NewGameUser.waiting_game_key)
async def gameuser_gamekey(message: types.Message, state: FSMContext):
    log.info('new_gs_link from: %r', message.from_user.id)
    game = market_bot.get_game_by_game_key(
        game_key=message.text
    )

    if not game:
        log.warning('wrong gamekey from: %r', message.from_user.id)
        await message.answer(
            get_text_from('./text_of_questions/game_key_wrong.txt'))
        return

    gameuser = game.add_gameuser(tg_id=message.from_user.id)
    gameuser.activate()
    await NewGameUser.next()
    await message.answer(
            get_text_from('./text_of_questions/game_key_correct.txt'))


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=NewGameUser.waiting_last_name)
async def gameuser_lastname(message: types.Message, state: FSMContext):
    log.info('gameuser_lastname from: %r', message.from_user.id)

    gameuser_id = market_bot.get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    gameuser.change_last_name(
        new_last_name=message.text
    )
    await NewGameUser.next()
    await message.answer(
            get_text_from('./text_of_questions/last_name_correct.txt'))


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=NewGameUser.waiting_first_name)
async def gameuser_firstname(message: types.Message, state: FSMContext):
    log.info('gameuser_firstname from: %r', message.from_user.id)

    gameuser_id = market_bot.get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    gameuser.change_first_name(
        new_first_name=message.text
    )
    await NewGameUser.next()
    await message.answer(
            get_text_from('./text_of_questions/first_name_correct.txt'))


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=NewGameUser.waiting_nickname)
async def gameuser_nickname(message: types.Message, state: FSMContext):
    log.info('gameuser_nickname from: %r', message.from_user.id)

    gameuser_id = market_bot.get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    if gameuser.is_nickname_unique(nickname=message.text):
        gameuser.change_nickname(
            new_nickname=message.text
        )
        await state.finish()
        keyboard = get_gameuser_keyboard()
        await message.answer(
            get_text_from('./text_of_questions/nickname_correct.txt'),
            reply_markup=keyboard
        )
        game = gameuser.get_game()
        game.add_gameuser_in_sheet(gameuser_id)
    else:
        log.info('wrong gameuser_nickname from: %r', message.from_user.id)
        await message.answer(
                get_text_from('./text_of_questions/nickname_wrong.txt'))


#  ---------------------------------------------------------- КЛАВИАТУРА ИГРОКА
market_button_word = 'Посмотреть на рынок'
portfolio_button_word = 'Мой портфель'
chart_button_word = 'Графики/Статистика'
how_to_use_button_word = 'Как пользоваться ботом?'
update_button = 'Обновить'

basemenu_list = [
    market_button_word,
    portfolio_button_word,
    chart_button_word,
    how_to_use_button_word,
    update_button
]


def get_gameuser_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in basemenu_list:
        keyboard.add(types.KeyboardButton(name))
    return keyboard


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
