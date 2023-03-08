import asyncio
import datetime
from typing import Union

from aiogram import types
from aiogram.utils import exceptions
from loguru import logger

from tgbot.loader import dp
from tgbot.config import TG_ADMINS_ID
from tgbot.utils.pars_messages import Post


async def send_messages(
        users_id: Union[list, str],
        text: str):
    await broadcast_post(
        post=Post(
            title=None,
            text=text,
            photos=[],
            video=None,
            docs=[],
            polls=[],
        ),
        users_id=users_id
    )


async def broadcast_post(
        post: Post,
        users_id: Union[list, str],
        reply_markup: types.InlineKeyboardMarkup = None,
        disable_web_page_preview=False,
        show_result=False):
    logger.info('started message sending')
    count = 0
    start_time = datetime.datetime.now()
    users_id = users_id if isinstance(users_id, list) else [users_id]
    for user_id in users_id:
        try:
            await send_post(
                post=post,
                tg_chat_id=user_id,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
            )
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
            await broadcast_post(
                post,
                users_id,
                reply_markup,
                disable_web_page_preview,
                show_result)
        except exceptions.UserDeactivated:
            logger.info(f"Target [ID:{user_id}]: user is deactivated")
        except exceptions.TelegramAPIError:
            logger.error(f"Target [ID:{user_id}]: failed")
        else:
            count += 1
            logger.info(f"Target [ID:{user_id}]: success")

    if show_result:
        return await create_result_text(start_time, users_id, count)


async def create_result_text(start_time, users_id, count):
    finish_time = datetime.datetime.now()
    total_time = (finish_time - start_time).total_seconds()
    msg = (
        f'Результаты рассылки:\n'
        f'Время начала рассылки - {start_time.time()}\n'
        f'Всего пользователей - {len(users_id)}\n'
        f'Отправлено сообщений - {count}\n'
        f'Время окончания рассылки - {finish_time}\n'
        f'Итоговое время рассылки, в сек. - {total_time}\n'
    )
    return msg


async def send_post(
        post: Post,
        tg_chat_id: int,
        reply_markup: types.InlineKeyboardMarkup = None,
        disable_web_page_preview: bool = False,
    ) -> None:

    if len(post.photos) == 1:
        await send_photo_post(
            post,
            tg_chat_id,
            reply_markup,
            disable_web_page_preview)
    elif len(post.photos) >= 2:
        await send_photos_post(
            post,
            tg_chat_id,
            reply_markup,
            disable_web_page_preview)
    elif post.video:
        await send_video_post(
            post,
            tg_chat_id,
            reply_markup,
            disable_web_page_preview)
    else:
        await send_text_post(
            post,
            tg_chat_id,
            reply_markup,
            disable_web_page_preview)

    if post.docs:
        await send_docs_post(post, tg_chat_id)
    if post.polls:
        pass

    logger.info(f"Post sended to {tg_chat_id}")
    

def split_text(text: str, fragment_size: int) -> list:
    fragments = []
    for fragment in range(0, len(text), fragment_size):
        fragments.append(text[fragment : fragment + fragment_size])
    return fragments


async def send_text_post(
        post: Post,
        tg_chat_id: int,
        reply_markup: types.InlineKeyboardMarkup = None,
        disable_web_page_preview: bool = False
    ) -> None:

    if not post.text:
        return

    if len(post.text) < 4096:
        await dp.bot.send_message(
            tg_chat_id,
            post.text,
            parse_mode=types.ParseMode.HTML,
            disable_web_page_preview=disable_web_page_preview,
            reply_markup=reply_markup)
    else:
        text_parts = split_text(post.text, 4084)
        prepared_text_parts = (
            [text_parts[0] + " (...)"]
            + ["(...) " + part + " (...)" for part in text_parts[1:-1]]
            + ["(...) " + text_parts[-1]]
        )

        for part in prepared_text_parts[:-1]:
            await dp.bot.send_message(
                tg_chat_id,
                part,
                parse_mode=types.ParseMode.HTML,
                disable_web_page_preview=disable_web_page_preview)
            await asyncio.sleep(0.5)
        # send last part
        await dp.bot.send_message(
            tg_chat_id,
            prepared_text_parts[-1],
            parse_mode=types.ParseMode.HTML,
            disable_web_page_preview=disable_web_page_preview)
    logger.info("Text post sent to Telegram.")


async def send_photo_post(
        post: Post,
        tg_chat_id: int,
        reply_markup: types.InlineKeyboardMarkup,
        disable_web_page_preview: bool,
) -> None:
    if len(post.text) <= 1024:
        await dp.bot.send_photo(
            tg_chat_id,
            post.photos[0],
            post.text,
            parse_mode=types.ParseMode.HTML,
            reply_markup=reply_markup,
        )
        logger.info("Text post (<=1024) with photo sent to Telegram.")
    else:
        prepared_text = f'<a href="{post.photos[0]}"> </a>{post.text}'
        if len(prepared_text) <= 4096:
            await dp.bot.send_message(
                tg_chat_id, prepared_text,
                parse_mode=types.ParseMode.HTML,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=reply_markup,
            )
        else:
            await dp.bot.send_photo(tg_chat_id, post.photos[0])
            await send_text_post(
                post,
                tg_chat_id,
                reply_markup,
                disable_web_page_preview)
        logger.info("Text post (>1024) with photo sent to Telegram.")


async def send_photos_post(
        post: Post,
        tg_chat_id: int,
        disable_web_page_preview: bool
) -> None:
    media = types.MediaGroup()
    for photo in post.photos:
        media.attach_photo(types.InputMediaPhoto(photo))

    if (len(post.text) > 0) and (len(post.text) <= 1024):
        media.media[0].caption = post.text
        media.media[0].parse_mode = types.ParseMode.HTML
    elif len(post.text) > 1024:
        await send_text_post(post, tg_chat_id, disable_web_page_preview)
    await dp.bot.send_media_group(tg_chat_id, media)
    logger.info("Text post with photos sent to Telegram.")


async def send_video_post(
        post: Post,
        tg_chat_id: int,
        reply_markup: types.InlineKeyboardMarkup,
        disable_web_page_preview: bool,
) -> None:
    if len(post.text) <= 1024:
        await dp.bot.send_video(
            tg_chat_id,
            post.video,
            caption=post.text,
            parse_mode=types.ParseMode.HTML,
            reply_markup=reply_markup,
        )
        logger.info("Text post (<=1024) with photo sent to Telegram.")
    else:
        await dp.bot.send_video(
            tg_chat_id,
            post.video,
        )
        await send_text_post(
            post,
            tg_chat_id,
            reply_markup,
            disable_web_page_preview)
        logger.info("Text post (>1024) with photo sent to Telegram.")


async def send_docs_post(post: Post, tg_chat_id: str) -> None:
    media = types.MediaGroup()
    for doc in post.docs:
        media.attach_document(
            types.InputMediaDocument(open(f"./temp/{doc['title']}", "rb"))
        )
    await dp.bot.send_media_group(tg_chat_id, media)
    logger.info("Documents sent to Telegram.")
