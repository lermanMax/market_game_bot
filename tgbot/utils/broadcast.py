import asyncio
import datetime
from typing import Union

from aiogram.utils import exceptions
from loguru import logger

from tgbot.loader import dp
from tgbot.config import TG_ADMINS_ID


async def send_messages(
        users_id: Union[list, str],
        message: str,
        keyboard=None,
        disable_web_page_preview=False,
        show_result=False):
    logger.info('started message sending')
    count = 0
    start_time = datetime.datetime.now()
    users_id = users_id if isinstance(users_id, list) else [users_id]
    for user_id in users_id:
        try:
            await dp.bot.send_message(
                chat_id=user_id,
                text=message,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=keyboard)
            await asyncio.sleep(0.04)  # Telegram limit 30 message per second
        except exceptions.BotBlocked:
            logger.info(f"Target [ID:{user_id}]: blocked by user")
        except exceptions.ChatNotFound:
            logger.info(f"Target [ID:{user_id}]: invalid user ID")
        except exceptions.RetryAfter as e:
            logger.info(
                f"Target [ID:{user_id}]: Flood limit is exceeded."
                f" Sleep {e.timeout} seconds.")
            await asyncio.sleep(e.timeout)
            await send_messages(
                user_id, message, keyboard, disable_web_page_preview)
        except exceptions.UserDeactivated:
            logger.info(f"Target [ID:{user_id}]: user is deactivated")
        except exceptions.TelegramAPIError:
            logger.error(f"Target [ID:{user_id}]: failed")
        else:
            count += 1
            logger.info(f"Target [ID:{user_id}]: success")

    if show_result:
        send_report_to_admins(start_time, users_id, count)


async def send_messages_to_admins(
        message: str,
        keyboard=None):
        return await send_messages(
            TG_ADMINS_ID, message, keyboard)


async def send_report_to_admins(start_time, users_id, count):
    finish_time = datetime.datetime.now()
    total_time = (finish_time - start_time).total_seconds()
    msg = f'Время начала рассылки - {start_time.time()}\n' \
            f'Всего пользователей - {len(users_id)}\n' \
            f'Отправлено сообщений - {count}\n' \
            f'Время окончания рассылки - {finish_time}' \
            f'Итоговое время рассылки, в сек. - {total_time}'
    return await send_messages_to_admins(msg)


async def send_photo(
        users_id: Union[list, str],
        message: str,
        photo,
        keyboard=None,
        retry=False,
        show_result=False):
    logger.info('started photo message sending')
    count = 0
    start_time = datetime.datetime.now()
    users_id = users_id if isinstance(users_id, list) else [users_id]
    for user_id in users_id:
        try:
            await dp.bot.send_photo(chat_id=user_id, photo=photo, caption=message, reply_markup=keyboard)
            await asyncio.sleep(0.05)  # Telegram limit 30 message per second, here set 20 msg per second
        except exceptions.BotBlocked:
            logger.info(f"Target [ID:{user_id}]: blocked by user")
        except exceptions.ChatNotFound:
            logger.info(f"Target [ID:{user_id}]: invalid user ID")
        except exceptions.RetryAfter as e:
            logger.info(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
            await asyncio.sleep(e.timeout)
            if not retry:
                await send_photo(user_id, message, photo, keyboard=keyboard, retry=True)
        except exceptions.UserDeactivated:
            logger.info(f"Target [ID:{user_id}]: user is deactivated")
        except exceptions.TelegramAPIError:
            logger.error(f"Target [ID:{user_id}]: failed")
        else:
            count += 1
            logger.info(f"Target [ID:{user_id}]: success")
    
    if show_result:
        send_report_to_admins(start_time, users_id, count)
