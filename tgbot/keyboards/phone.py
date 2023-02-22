from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def phone_markup() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton(
                    text='📞 Поделиться номером', request_contact=True
                )
            ],
        ],
    )
    return keyboard

phone_keyboard = phone_markup()
