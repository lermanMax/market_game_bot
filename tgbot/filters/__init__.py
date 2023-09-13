from aiogram import Dispatcher

from .admin import IsAdminUserFilter
from .content import TextNotComand


def setup(dp: Dispatcher):
    dp.filters_factory.bind(
        IsAdminUserFilter,
        event_handlers=dp.message_handlers
    )
    dp.filters_factory.bind(
        TextNotComand,
        event_handlers=dp.message_handlers
    )

