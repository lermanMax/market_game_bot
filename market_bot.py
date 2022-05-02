from email.message import Message
import logging
from random import randrange
import typing

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import callback_data
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Import modules of this project
from config import API_TOKEN, SUPERADMIN_PASS, BOT_MAILADDRESS
from schedule_module import schedule, run_continuously
from business_logic import Company, DealIllegal, Game, MarketBot, \
    NotEnoughMoney, SuperAdmin, GameUser

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('market_bot')

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# Sructure of callback buttons
button_cb = callback_data.CallbackData(
    'btn', 'question_name', 'answer', 'data')

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


@dp.message_handler(commands=['start'], state="*")
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


@dp.message_handler(commands=['help'], state="*")
async def send_help(message: types.Message, state: FSMContext):
    log.info('help command from: %r', message.from_user.id)
    gameuser_id = market_bot.get_active_gameuser_id_for(message.from_user.id)
    await state.finish()
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
            game.load_companes_from_sheet()
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
        schedule.every(20).seconds.do(
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

buy_button = 'Купить'
sell_button = 'Продать'
cancel_button = 'Отменить сделку'

gameuser_buttons_list = [
    market_button_word,
    portfolio_button_word,
    chart_button_word,
    how_to_use_button_word,
    update_button
]


def get_gameuser_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in gameuser_buttons_list:
        keyboard.add(types.KeyboardButton(name))
    return keyboard


def make_inline_keyboard(question_name, answers, data=0):
    """Возвращает клавиатуру для сообщений"""
    if not answers:
        return None

    keyboard = types.InlineKeyboardMarkup()
    row = []
    for answer in answers:  # make a botton for every answer
        cb_data = button_cb.new(
            question_name=question_name,
            answer=answer,
            data=data)
        row.append(types.InlineKeyboardButton(answer,
                                              callback_data=cb_data))
    if len(row) <= 2:
        keyboard.row(*row)
    else:
        for button in row:
            keyboard.row(button)

    return keyboard


def make_keyboard_for_company(company_id: int):
    keyboard = make_inline_keyboard(
        question_name='market_deal',
        answers=[buy_button, sell_button],
        data=company_id
    )
    return keyboard


def make_keyboard_for_deal():
    keyboard = make_inline_keyboard(
        question_name='cancel',
        answers=[cancel_button]
    )
    return keyboard


async def send_market(message: types.Message, gameuser: GameUser):
    logging.info('send_market to: %r', message.from_user.id)
    game = gameuser.get_game()
    is_market_open = game.is_market_open_now()

    cash = gameuser.get_cash()
    if is_market_open:
        market_closed = ''
    else:
        market_closed = '\n<b>Рынок закрыт</b>'

    text = (
        'Это список всех компаний.'
        f'\nВаши свободные средства: { cash }'
        f'{ market_closed }'
    )
    await message.answer(
        text=text,
        reply_markup=get_gameuser_keyboard()
    )
    companes = game.get_list_of_companyes()
    for company in companes:
        count = len(
            gameuser.get_list_of_shares(
                company_id=company.get_id()
            )
        )
        text = (
            f'📈 <b>{ company.get_name() }</b> ({ company.get_ticker() })'
            f'\nЦена: {company.get_price()}'
            f'\nУ вас в портфеле этих акций: { count }'
        )
        if is_market_open:
            keyboard = make_keyboard_for_company(company.get_id())
        else:
            keyboard = None
        await message.answer(
            text=text,
            reply_markup=keyboard
        )


async def send_gameuser_partfolio(message: types.Message, gameuser: GameUser):
    logging.info('send_gameuser_partfolio to: %r', message.from_user.id)
    size = gameuser.get_portfolio_size()

    text = (
        f'Оценка портфеля: { size }'
        f'\nСвободные средства: { gameuser.get_cash() }'
        '\n------------------'
    )
    shares_dict = {}
    for share in gameuser.get_list_of_shares():
        if share.get_company_id() in shares_dict:
            shares_dict[share.get_company_id()] += 1
        else:
            shares_dict[share.get_company_id()] = 1

    for company_id, number in shares_dict.items():
        company = Company.get(company_id)
        s = f'\n{company.get_ticker()} - {number} - {company.get_price()}'
        text += s
    await message.answer(
        text=text,
        reply_markup=get_gameuser_keyboard()
    )


async def send_gameuser_chart_link(message: types.Message, gameuser: GameUser):
    logging.info('send_gameuser_chart_link to: %r', message.from_user.id)
    gameuser_id = market_bot.get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    game = gameuser.get_game()

    text = (
        f'Ссылка на графики: { game.get_chart_link() }'
    )

    await message.answer(
        text=text,
        reply_markup=get_gameuser_keyboard()
    )


async def send_gameuser_help(message: types.Message, gameuser: GameUser):
    logging.info('send_gameuser_help to: %r', message.from_user.id)
    gameuser_id = market_bot.get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    game = gameuser.get_game()

    text = (
        'Инструкция как нажимать / куда покупать'
        f'\nСсылка на администратора: { game.get_admin_contact() }'
    )

    await message.answer(
        text=text,
        reply_markup=get_gameuser_keyboard()
    )


async def send_gameuser_keyboard(message: types.Message, gameuser: GameUser):
    logging.info('send_gameuser_keyboard to: %r', message.from_user.id)
    await message.answer(
        text='Клавиатура обновлена',
        reply_markup=get_gameuser_keyboard()
    )


gameuser_buttons_dict = {
    market_button_word: send_market,
    portfolio_button_word: send_gameuser_partfolio,
    chart_button_word: send_gameuser_chart_link,
    how_to_use_button_word: send_gameuser_help,
    update_button: send_gameuser_keyboard
}


@dp.message_handler(
    lambda message: message.text in gameuser_buttons_list,
    state='*')
async def gameuser_keyboard(message: types.Message, state: FSMContext):
    """
    Получаем нажатие кнопки из клавиатуры игрока
    """
    logging.info('push gameuser_keyboard from: %r', message.from_user.id)

    gameuser_id = market_bot.get_active_gameuser_id_for(message.from_user.id)
    if gameuser_id:
        gameuser = GameUser.get(gameuser_id)
    else:
        logging.error('push button from unkown user: %r', message.from_user.id)
        return

    await gameuser_buttons_dict[message.text](
        message=message,
        gameuser=gameuser
    )


class MarketDeal(StatesGroup):
    waiting_number_shares = State()


@dp.callback_query_handler(
    button_cb.filter(question_name=['market_deal']),
    state='*')
async def callback_market_deal(
        query: types.CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    logging.info('Got this callback data: %r', callback_data)

    gameuser_id = market_bot.get_active_gameuser_id_for(query.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    game = gameuser.get_game()

    if not game.is_market_open_now():
        await query.message.answer(
            get_text_from('./text_of_questions/market_is_close.txt'))
        return

    company = Company.get(callback_data['data'])
    if callback_data['answer'] == buy_button:
        text = (
            '<b>Введите число</b> акций'
            f' { company.get_name() } ({ company.get_ticker() })'
            ' которое вы хотите купить?'
            f'\nЦена за штуку: {company.get_price()}'
            f'\nВаши свободные средства: { gameuser.get_cash() }'
        )
    elif callback_data['answer'] == sell_button:
        count = len(
            gameuser.get_list_of_shares(
                company_id=company.get_id()
            )
        )
        if count == 0:
            await query.message.answer(
                get_text_from('./text_of_questions/dont_have_shares.txt'))
            return
        text = (
            '<b>Введите число</b> акций'
            f' { company.get_name() } ({ company.get_ticker() })'
            ' которое вы хотите продать?'
            f'\nЦена за штуку: {company.get_price()}'
            f'\nУ вас в портфеле этих акций: { count }'
        )
    await MarketDeal.waiting_number_shares.set()
    await query.answer()
    msg = await query.message.answer(
        text=text, reply_markup=make_keyboard_for_deal())
    await state.update_data(answer=callback_data['answer'])
    await state.update_data(data_=callback_data['data'])
    await state.update_data(message_id=msg.message_id)


async def pashalka(message: Message):
    if randrange(0, 21, 1) == 20:
        await message.answer(text='ГАЛЯ, отмена!')


@dp.callback_query_handler(
    button_cb.filter(question_name=['cancel']),
    state='*')
async def callback_cancel_deal(
        query: types.CallbackQuery,
        callback_data: typing.Dict[str, str],
        state: FSMContext):
    logging.info('Got this callback data: %r', callback_data)

    if callback_data['answer'] == cancel_button:
        await pashalka(query.message)
        await query.message.delete()
        await state.finish()


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=MarketDeal.waiting_number_shares)
async def number_of_shares(message: types.Message, state: FSMContext):
    log.info('number_of_shares from: %r', message.from_user.id)
    try:
        number = int(message.text)
        if not number > 0:
            await message.answer(
                text='Введите целое число больше нуля:')
            return
    except Exception:
        await message.answer(
            text='Введите целое число больше нуля:')
        return
    state_data = await state.get_data()

    gameuser_id = market_bot.get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    game = gameuser.get_game()
    company = Company.get(state_data['data_'])

    if not game.is_market_open_now():
        await message.answer(
            get_text_from('./text_of_questions/market_is_close.txt'))
        return

    if state_data['answer'] == buy_button:
        try:
            game.buy_deal(
                buyer=gameuser,
                company=company,
                shares_number=number
            )
            text_was_sold = ''
        except NotEnoughMoney:
            await message.answer(
                get_text_from(
                    './text_of_questions/not_enough_money_for_buy.txt'))
            return
        except DealIllegal:
            await message.answer(
                get_text_from(
                    './text_of_questions/you_want_to_many.txt'))
            return
    elif state_data['answer'] == sell_button:
        real_number = game.sell_deal(
            seller=gameuser,
            company=company,
            shares_number=number
        )
        text_was_sold = f'\nБыло продано: { real_number }'
    await state.finish()
    count = len(
        gameuser.get_list_of_shares(
            company_id=company.get_id()
        )
    )

    text = (
        'Торговая сделка успешно совершена.'
        f'\n{ company.get_name() } ({ company.get_ticker() })'
        f'{ text_was_sold }'
        f'\nТеперь у вас в портфеле этих акций: { count }'
        f'\nВаши свободные средства: { gameuser.get_cash() }'
    )
    await bot.delete_message(
        chat_id=message.from_user.id,
        message_id=state_data['message_id'])
    await message.answer(
        text=text,
        reply_markup=get_gameuser_keyboard()
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
