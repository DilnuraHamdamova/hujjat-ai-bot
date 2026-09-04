import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.bot.commands import default_commands
from app.bot.setup import bot, dispatcher
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.ensure_valid_runtime()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)

    # MVP bootstrap. Production deployments should apply Alembic before app startup.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    await bot.set_my_commands(default_commands())
    logger.info("Telegram command menu configured")

    polling_task: asyncio.Task[None] | None = None
    if settings.bot_mode == "webhook":
        await bot.set_webhook(
            settings.webhook_url,
            secret_token=settings.webhook_secret.get_secret_value(),
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
        logger.info("Telegram webhook configured")
    else:
        await bot.delete_webhook(drop_pending_updates=False)
        polling_task = asyncio.create_task(
            dispatcher.start_polling(bot, handle_signals=False),
            name="telegram-polling",
        )
        logger.info("Telegram polling started")

    yield

    if polling_task:
        polling_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await polling_task
    await bot.session.close()
    await dispatcher["ai_provider"].aclose()
    await engine.dispose()


app = FastAPI(
    title="CV Telegram Bot",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url=None,
    lifespan=lifespan,
)
app.include_router(api_router)
