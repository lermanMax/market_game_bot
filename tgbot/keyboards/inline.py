from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import callback_data

# Sructure of callback buttons
button_cb = callback_data.CallbackData(
    'btn', 'question_name', 'answer', 'data')


async def make_inline_keyboard(question_name, answers, data=0):
    """Возвращает клавиатуру для сообщений"""
    if not answers:
        return None

    keyboard = InlineKeyboardMarkup()
    row = []
    for answer in answers:  # make a botton for every answer
        cb_data = button_cb.new(
            question_name=question_name,
            answer=answer,
            data=data)
        row.append(InlineKeyboardButton(answer,
                                              callback_data=cb_data))
    if len(row) <= 2:
        keyboard.row(*row)
    else:
        for button in row:
            keyboard.row(button)

    return keyboard


def get_choice_city_keyboard() -> InlineKeyboardMarkup:
    choice_city_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Санкт-Петербург", callback_data=choice_city_cb.new(city='Санкт-Петербург')),
            ],
            [
                InlineKeyboardButton(text="Нижний Новгород", callback_data=choice_city_cb.new(city='Нижний Новгород')),
            ],
            [
                InlineKeyboardButton(text="Челябинск", callback_data=choice_city_cb.new(city='Челябинск')),
            ],
            [
                InlineKeyboardButton(text="Екатеринбург", callback_data=choice_city_cb.new(city='Екатеринбург')),
            ],
            [
                InlineKeyboardButton(text="Нет моего города", callback_data=choice_city_cb.new(city='no_user_city')),
            ]
        ]
    )
    return choice_city_keyboard
