from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def start_markup() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton('/start'),
            ],
        ]
    )
    return keyboard

start_keyboard=start_markup()
