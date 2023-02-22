from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from tgbot.keyboards.inline import make_inline_keyboard


market_button_word = 'Рынок 🏛️'
portfolio_button_word = 'Мой портфель 💼'
chart_button_word = 'Информация и графики 📊'
how_to_use_button_word = 'Как пользоваться ботом❓'
update_button_word = 'Обновить 🔄'

buy_button = 'Купить'
sell_button = 'Продать'
cancel_button = 'Отменить сделку'

gameuser_buttons_list = [
    market_button_word,
    portfolio_button_word,
    chart_button_word,
    how_to_use_button_word
]


def get_gameuser_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton(market_button_word),
                KeyboardButton(portfolio_button_word),
            ],
            [
                KeyboardButton(chart_button_word),
            ],
            [
                KeyboardButton(how_to_use_button_word),
            ],
        ]
    )
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


gameuser_keyboard = get_gameuser_keyboard()
