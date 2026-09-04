from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import router
from app.core.config import get_settings
from app.db.middleware import DatabaseSessionMiddleware
from app.services.ai import DisabledAIProvider, GeminiProvider

settings = get_settings()
bot = Bot(
    token=settings.bot_token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dispatcher = Dispatcher()
dispatcher.update.outer_middleware(DatabaseSessionMiddleware())

gemini_api_key = settings.gemini_api_key.get_secret_value()
if gemini_api_key:
    dispatcher["ai_provider"] = GeminiProvider(
        api_key=gemini_api_key,
        model=settings.gemini_model,
        router_model=settings.gemini_router_model,
        voice_model=settings.gemini_voice_model,
    )
else:
    dispatcher["ai_provider"] = DisabledAIProvider()

dispatcher.include_router(router)
