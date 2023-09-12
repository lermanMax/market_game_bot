from random import randrange
from typing import List, Dict
import time
from loguru import logger

from aiogram import Bot, Dispatcher, executor, types

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Import modules of this project
from tgbot.loader import dp, bot
from tgbot.keyboards.inline import make_inline_keyboard, button_cb
from tgbot.keyboards.gameuser import gameuser_keyboard, \
    make_keyboard_for_deal, make_keyboard_for_company, \
    market_button_word, portfolio_button_word, chart_button_word, \
    how_to_use_button_word, update_button_word, gameuser_buttons_list, \
    buy_button, sell_button, cancel_button
    
from tgbot.utils.file_manager import get_text_from
from tgbot.services.business_logic import Company, DealIllegal, Game, MarketBot, \
    NotEnoughMoney, SuperAdmin, GameUser, TgUser


#  ---------------------------------------------------------- КЛАВИАТУРА ИГРОКА


async def send_market(message: types.Message, gameuser: GameUser):
    logger.info(f'send_market to: {message.from_user.id}')
    game = gameuser.get_game()
    is_market_open = game.is_market_open_now()

    cash = gameuser.get_cash()
    if is_market_open:
        market_closed = '\nРынок открыт'
    else:
        market_closed = '\n<b>Рынок закрыт</b>'

    text = (
        'Это список всех компаний.'
        f'\nВаш баланс: { round(cash) }'
        f'{ market_closed }'
    )
    await message.answer(
        text=text,
        reply_markup=gameuser_keyboard
    )
    companes = game.get_list_of_actual_companyes()
    for company in companes:
        count = len(
            gameuser.get_list_of_shares(
                company_id=company.get_id()
            )
        )
        text = (
            f'📈 <b>{ company.get_name() }</b> ({ company.get_ticker() })'
            f'\nЦена: {round(company.get_price())}'
            f'\nУ вас в портфеле этих акций: { count }'
        )
        if is_market_open:
            keyboard = await make_keyboard_for_company(company.get_id())
        else:
            keyboard = None
        await message.answer(
            text=text,
            reply_markup=keyboard
        )


async def send_gameuser_partfolio(message: types.Message, gameuser: GameUser):
    logger.info(f'send_gameuser_partfolio to: {message.from_user.id}')
    size = gameuser.get_portfolio_size()

    text = (
        f'Оценка портфеля: { round(size) }'
        f'\nСвободные средства: { round(gameuser.get_cash()) }'
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
        s = f'\n{company.get_ticker()} - {number} - {round(company.get_price())}'
        text += s
    await message.answer(
        text=text,
        reply_markup=gameuser_keyboard
    )


async def send_gameuser_chart_link(message: types.Message, gameuser: GameUser):
    logger.info(f'send_gameuser_chart_link to: {message.from_user.id}')
    gameuser_id = MarketBot().get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    game = gameuser.get_game()

    text = (
        'Здесть публикуются ссылки на графики и статистику по рынку'
    )
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(
        'Посмотреть статистику',
        url=f'{ game.get_chart_link() }'
    ))

    await message.answer(
        text=text,
        reply_markup=keyboard
    )


async def send_gameuser_help(message: types.Message, gameuser: GameUser):
    logger.info(f'send_gameuser_help to: {message.from_user.id}')
    gameuser_id = MarketBot().get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    game = gameuser.get_game()

    text = (
        f'{ get_text_from("./tgbot/text_of_questions/instruction.txt") }'
        f'\nСсылка на администратора: { game.get_admin_contact() }'
    )
    await message.answer(
        text=text,
        reply_markup=gameuser_keyboard
    )

    FAQ_text = 'Часто задаваемые вопросы:'
    for QA_dict in game.get_FAQ():
        FAQ_text += (
            f"\n\n◾ <b>{ QA_dict['question'] }</b>"
            f"\n{ QA_dict['answer'] }"
        )
    await message.answer(
        text=FAQ_text,
        reply_markup=gameuser_keyboard
    )


async def send_gameuser_keyboard(message: types.Message, gameuser: GameUser):
    logger.info(f'send_gameuser_keyboard to: {message.from_user.id}')
    await message.answer(
        text='Клавиатура обновлена',
        reply_markup=gameuser_keyboard
    )


gameuser_buttons_dict = {
    market_button_word: send_market,
    portfolio_button_word: send_gameuser_partfolio,
    chart_button_word: send_gameuser_chart_link,
    how_to_use_button_word: send_gameuser_help,
    update_button_word: send_gameuser_keyboard
}


@dp.message_handler(
    lambda message: message.text in gameuser_buttons_list,
    state='*')
async def gameuser_keyboard_push(message: types.Message, state: FSMContext):
    """
    Получаем нажатие кнопки из клавиатуры игрока
    """
    logger.info(f'push gameuser_keyboard from: {message.from_user.id}')
    
    gameuser_id = MarketBot().get_active_gameuser_id_for(message.from_user.id)
    if gameuser_id:
        gameuser = GameUser.get(gameuser_id)
    else:
        logger.error(f'push button from unkown user: {message.from_user.id}')
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
        callback_data: Dict[str, str],
        state: FSMContext):
    logger.info(f'Got this callback data: {callback_data}')
    
    gameuser_id = MarketBot().get_active_gameuser_id_for(query.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    game = gameuser.get_game()

    if not game.is_market_open_now():
        await query.message.answer(
            get_text_from('./tgbot/text_of_questions/market_is_close.txt'))
        return

    company = Company.get(callback_data['data'])
    if company.get_price() == 0:
        await query.message.answer(
            get_text_from('./tgbot/text_of_questions/company_was_liquidated.txt'))
        return
    if callback_data['answer'] == buy_button:
        text = (
            '<b>Введи количество</b> акций'
            f' { company.get_name() } ({ company.get_ticker() })'
            ' которое хочешь купить.'
            f'\nСтоимость одной акции: {round(company.get_price())}'
            f'\nВаши свободные средства: { round(gameuser.get_cash()) }'
        )
    elif callback_data['answer'] == sell_button:
        count = len(
            gameuser.get_list_of_shares(
                company_id=company.get_id()
            )
        )
        if count == 0:
            await query.message.answer(
                get_text_from('./tgbot/text_of_questions/dont_have_shares.txt'))
            return
        text = (
            '<b>Введи количество</b> акций'
            f' { company.get_name() } ({ company.get_ticker() })'
            ' которое хочешь продать?'
            f'\nСтоимость одной акции: {round(company.get_price())}'
            f'\nВ портфеле этих акций: { count }'
        )
    await MarketDeal.waiting_number_shares.set()
    await query.answer()
    msg = await query.message.answer(
        text=text,
        reply_markup=await make_keyboard_for_deal())
    await state.update_data(answer=callback_data['answer'])
    await state.update_data(data_=callback_data['data'])
    await state.update_data(message_id=msg.message_id)


async def pashalka(message: types.Message):
    if randrange(0, 21, 1) == 20:
        await message.answer(text='ГАЛЯ, отмена!')


@dp.callback_query_handler(
    button_cb.filter(question_name=['cancel']),
    state='*')
async def callback_cancel_deal(
        query: types.CallbackQuery,
        callback_data: Dict[str, str],
        state: FSMContext):
    logger.info(f'Got this callback data: {callback_data}')
    
    if callback_data['answer'] == cancel_button:
        await pashalka(query.message)
        await query.message.delete()
        await state.finish()


@dp.message_handler(
    content_types=types.message.ContentType.TEXT,
    state=MarketDeal.waiting_number_shares)
async def number_of_shares(message: types.Message, state: FSMContext):
    logger.info(f'number_of_shares from: {message.from_user.id}')

    try:
        number = int(message.text)
        if not number > 0:
            await message.answer(
                text=get_text_from('./tgbot/text_of_questions/wrong_number.txt'))
            return
    except Exception:
        await message.answer(
            text=get_text_from('./tgbot/text_of_questions/wrong_number.txt'))
        return
    state_data = await state.get_data()

    gameuser_id = MarketBot().get_active_gameuser_id_for(message.from_user.id)
    gameuser = GameUser.get(gameuser_id)
    game = gameuser.get_game()
    company = Company.get(state_data['data_'])

    if not game.is_market_open_now():
        await message.answer(
            get_text_from('./tgbot/text_of_questions/market_is_close.txt'))
        return

    if state_data['answer'] == buy_button:
        try:
            game.buy_deal(
                buyer=gameuser,
                company=company,
                shares_number=number
            )
            text_was_sold = f'Успешная покупка {number} акций(я) компании '
        except NotEnoughMoney:
            await message.answer(
                get_text_from(
                    './tgbot/text_of_questions/not_enough_money_for_buy.txt'))
            return
        except DealIllegal:
            await message.answer(
                text=(
                    'Твой портфель не будет удовлетворять условиям, '
                    'заданным администратором игры: '
                    'после покупки <b>одна компания не может занимать больше '
                    f'{ game.get_max_percentage() }% портфеля.</b>'
                    '\nУкажи другое число.'
                ))
            return
    elif state_data['answer'] == sell_button:
        real_number = game.sell_deal(
            seller=gameuser,
            company=company,
            shares_number=number
        )
        text_was_sold = f'Успешно продано {real_number} акций(я) компании'
    await state.finish()
    count = len(
        gameuser.get_list_of_shares(
            company_id=company.get_id()
        )
    )

    text = (
        f'{text_was_sold}'
        f'{ company.get_name() } ({ company.get_ticker() }).'
        f'\n\nТеперь в портфеле этих акций: { count }'
        f'\nВаш баланс: { round(gameuser.get_cash()) }'
    )
    await bot.delete_message(
        chat_id=message.from_user.id,
        message_id=state_data['message_id'])
    await message.answer(
        text=text,
        reply_markup=gameuser_keyboard
    )
