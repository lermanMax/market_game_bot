from aiogram import Dispatcher
from aiogram import executor, types
from loguru import logger
import os

from tgbot.config import GSHEET_SERVICE_FILE, BOT_MAILADDRESS
from tgbot.utils.broadcast import send_messages
from tgbot.config import TG_ADMINS_ID
from tgbot.services.business_logic import MarketBot
from tgbot.loader import scheduler


async def setup_default_commands(dp: Dispatcher):
    await dp.bot.set_my_commands(
        [
            types.BotCommand('help', 'помощь')
        ]
    )
    logger.info('Default commands soccessfully set')


async def on_startup_polling(dp: Dispatcher):
    logger.info('Start on polling mode')

    await setup_default_commands(dp)

    from tgbot import handlers

    from tgbot import middlewares

    # Check after reboot
    MarketBot().check_games_and_create_schedule()

    await send_messages(TG_ADMINS_ID, 'startup')


async def on_shutdown(dp: Dispatcher):
    logger.info('Shutdown')

    scheduler.shutdown()
    logger.info('scheduler shutdown')


def polling(skip_updates: bool = False):
    from tgbot.handlers import dp
    executor.start_polling(
        dispatcher=dp,
        skip_updates=skip_updates,
        on_startup=on_startup_polling,
        on_shutdown=on_shutdown
    )


if __name__ == '__main__':
    polling()
