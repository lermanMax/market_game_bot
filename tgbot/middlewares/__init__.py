from loguru import logger

from tgbot.loader import dp

from .authentification import AccessMiddleware

if __name__ == "tgbot.middlewares":
    dp.middleware.setup(AccessMiddleware())
    logger.info('Middlewares configured')
