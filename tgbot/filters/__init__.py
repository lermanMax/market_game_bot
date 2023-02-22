from aiogram import Dispatcher

from .admin import IsAdminUserFilter


def setup(dp: Dispatcher):
    dp.filters_factory.bind(
        IsAdminUserFilter,
        event_handlers=dp.message_handlers
    )
