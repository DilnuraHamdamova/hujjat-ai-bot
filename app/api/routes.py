import logging

from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Response, status
from sqlalchemy import delete, text
from sqlalchemy.exc import IntegrityError

from app.bot.setup import bot, dispatcher
from app.core.config import get_settings
from app.db.models import ProcessedUpdate
from app.db.session import SessionFactory

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    async with SessionFactory() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.post(settings.webhook_path, include_in_schema=False)
async def telegram_webhook(
    update: Update,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> Response:
    if settings.bot_mode != "webhook":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if x_telegram_bot_api_secret_token != settings.webhook_secret.get_secret_value():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    async with SessionFactory() as session:
        session.add(ProcessedUpdate(update_id=update.update_id))
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return Response(status_code=status.HTTP_200_OK)

    try:
        await dispatcher.feed_update(bot, update)
    except Exception:
        logger.exception("Telegram update processing failed", extra={"update_id": update.update_id})
        async with SessionFactory() as session:
            await session.execute(
                delete(ProcessedUpdate).where(ProcessedUpdate.update_id == update.update_id)
            )
            await session.commit()
        raise
    return Response(status_code=status.HTTP_200_OK)
