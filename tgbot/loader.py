from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from tgbot.config import TGBOT_TOKEN

# Setup storage
storage = MemoryStorage()

# Setup bot
bot = Bot(token=TGBOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)

# Setup middlewares
# from tgbot import middlewares

# Setup scheduler
scheduler = AsyncIOScheduler()
scheduler.start()
