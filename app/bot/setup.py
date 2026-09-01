from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import router
from app.core.config import get_settings
from app.db.middleware import DatabaseSessionMiddleware

settings = get_settings()
bot = Bot(
    token=settings.bot_token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dispatcher = Dispatcher()
dispatcher.update.outer_middleware(DatabaseSessionMiddleware())
dispatcher.include_router(router)
