from typing import List, Dict, NamedTuple
from loguru import logger

from aiogram.types import Message

# class for post message for telegram bot
class Post(NamedTuple):
    title: str
    text: str
    photos: List[str]
    video: str
    docs: List[str]
    polls: List[Dict[str, str]]


async def parse_message(message: Message, title: str=None) -> Post:
    """parse telegram message and return Post object

    Args:
        message (Message): message for parsing
        title (str, optional): bold title for post. Defaults to None.

    Returns:
        Post: _description_
    """
    logger.info(f"Parsing message: ...")
    if message.text:
        text = message.text
    elif message.caption:
        text = message.caption
    else:
        text = ''
    photos = []
    docs = []
    polls = []
    if message.photo:
        photos.append(message.photo[-1].file_id)

    if message.video:
        video = message.video.file_id
    else:
        video = None

    if message.document:
        doc = message.document.file_id
    else:
        doc = None
    

    return Post(title, text, photos, video, docs, polls)




    

