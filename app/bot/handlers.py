import asyncio
import logging
import shutil
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.types import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import (
    delete_confirmation_keyboard,
    edit_fields_keyboard,
    review_keyboard,
    start_keyboard,
)
from app.core.config import get_settings
from app.db.models import User
from app.documents.generator import DocumentGenerator
from app.repositories.resumes import (
    create_resume,
    delete_user_data,
    get_current_resume,
    get_or_create_user,
    get_user_document_paths,
    mark_completed,
    save_answer,
    save_document,
    set_editing_step,
)
from app.services.resume_flow import (
    STEP_BY_KEY,
    STEPS,
    build_preview,
    next_step,
    parse_answer,
    split_preview,
    validate_answer,
)

logger = logging.getLogger(__name__)
router = Router(name="resume")


async def _user(session: AsyncSession, telegram_user: TelegramUser) -> User:
    return await get_or_create_user(
        session,
        telegram_user_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        language_code=telegram_user.language_code,
    )


@router.message(CommandStart())
async def start(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    await _user(session, message.from_user)
    await message.answer(
        "<b>CV Builder botiga xush kelibsiz!</b>\n\n"
        "Men savollarni ketma-ket beraman. Siz matn orqali javob berasiz, "
        "yakunda PDF va Word formatidagi CV olasiz.",
        reply_markup=start_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "<b>Buyruqlar</b>\n"
        "/start — asosiy menyu\n"
        "/new — yangi CV\n"
        "/my_cv — oxirgi CV\n"
        "/delete_me — barcha ma’lumotlarni o‘chirish"
    )


@router.message(Command("new"))
async def new_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user = await _user(session, message.from_user)
    await create_resume(session, user.id)
    await message.answer(STEPS[0].prompt)


@router.callback_query(F.data == "resume:new")
async def new_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    await create_resume(session, user.id)
    await callback.answer()
    if callback.message:
        await callback.message.answer(STEPS[0].prompt)


async def _show_last(message: Message, session: AsyncSession, telegram_user: TelegramUser) -> None:
    user = await _user(session, telegram_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or not draft.data:
        await message.answer("Hali CV yaratilmagan.", reply_markup=start_keyboard())
        return
    await _send_preview(message, draft.data)


async def _send_preview(message: Message, data: dict[str, object]) -> None:
    chunks = split_preview(build_preview(data))
    for chunk in chunks[:-1]:
        await message.answer(chunk)
    await message.answer(chunks[-1], reply_markup=review_keyboard())


@router.message(Command("my_cv"))
async def my_cv_command(message: Message, session: AsyncSession) -> None:
    if message.from_user:
        await _show_last(message, session, message.from_user)


@router.callback_query(F.data == "resume:last")
async def last_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await _show_last(callback.message, session, callback.from_user)


@router.callback_query(F.data == "resume:edit")
async def edit_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Qaysi ma’lumotni o‘zgartirmoqchisiz?", reply_markup=edit_fields_keyboard()
        )


@router.callback_query(F.data.startswith("resume:field:"))
async def edit_field_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    step_key = callback.data.rsplit(":", 1)[-1]
    step = STEP_BY_KEY.get(step_key)
    if step is None:
        await callback.answer("Noto‘g‘ri maydon", show_alert=True)
        return
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None:
        await callback.answer("CV topilmadi", show_alert=True)
        return
    await set_editing_step(session, draft, step.key)
    await callback.answer()
    if callback.message:
        await callback.message.answer(step.prompt)


@router.message(F.voice | F.audio)
async def voice_not_enabled(message: Message) -> None:
    await message.answer(
        "Ovozli xabar funksiyasi keyingi bosqichda OpenAI bilan ulanadi. "
        "Hozir javobni matn ko‘rinishida yuboring."
    )


@router.message(F.text & ~F.text.startswith("/"))
async def collect_text(message: Message, session: AsyncSession) -> None:
    if message.from_user is None or message.text is None:
        return
    user = await _user(session, message.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status not in ("collecting", "editing"):
        await message.answer("Avval yangi CV yaratishni boshlang.", reply_markup=start_keyboard())
        return

    step = STEP_BY_KEY.get(draft.current_step)
    if step is None:
        await message.answer("Jarayon holati buzilgan. /new orqali qayta boshlang.")
        return

    validation_error = validate_answer(step, message.text)
    if validation_error:
        await message.answer(validation_error)
        return

    was_editing = draft.status == "editing"
    following_step = None if was_editing else next_step(step.key)
    draft = await save_answer(
        session,
        draft,
        key=step.key,
        value=parse_answer(step, message.text),
        next_step_key=following_step.key if following_step else None,
    )

    if draft.status == "review":
        await _send_preview(message, draft.data)
    elif following_step:
        await message.answer(following_step.prompt)


@router.callback_query(F.data == "resume:approve")
async def approve_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status not in ("review", "completed"):
        await callback.answer("Tasdiqlash uchun tayyor CV topilmadi", show_alert=True)
        return

    await callback.answer("Hujjatlar tayyorlanmoqda...")
    if callback.message is None:
        return
    status_message = await callback.message.answer("⏳ PDF va Word yaratilmoqda...")
    try:
        generator = DocumentGenerator(get_settings().storage_dir)
        artifacts = await asyncio.to_thread(generator.generate, draft.id, draft.data)
        for artifact in artifacts:
            await save_document(
                session,
                resume_id=draft.id,
                file_format=artifact.format,
                storage_key=str(artifact.path),
                checksum=artifact.checksum,
            )
        await mark_completed(session, draft)

        for artifact in artifacts:
            filename = f"CV.{artifact.format}"
            await callback.message.answer_document(
                FSInputFile(artifact.path, filename=filename),
                caption=f"✅ {filename} tayyor",
            )
        await status_message.edit_text("✅ CV muvaffaqiyatli tayyorlandi.")
    except Exception:
        logger.exception("Document generation failed", extra={"resume_id": str(draft.id)})
        await status_message.edit_text(
            "Hujjat yaratishda xatolik yuz berdi. Birozdan keyin qayta urinib ko‘ring."
        )


@router.message(Command("delete_me"))
async def delete_me_command(message: Message) -> None:
    await message.answer(
        "Barcha CV, hujjat va profilingiz o‘chirilsinmi? Bu amalni qaytarib bo‘lmaydi.",
        reply_markup=delete_confirmation_keyboard(),
    )


@router.callback_query(F.data == "privacy:cancel")
async def delete_cancel(callback: CallbackQuery) -> None:
    await callback.answer("Bekor qilindi")
    if isinstance(callback.message, Message):
        await callback.message.edit_text("Ma’lumotlaringiz saqlab qolindi.")


@router.callback_query(F.data == "privacy:delete")
async def delete_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    paths = await get_user_document_paths(session, callback.from_user.id)
    await delete_user_data(session, callback.from_user.id)
    for raw_path in paths:
        path = Path(raw_path)
        if path.parent.exists():
            shutil.rmtree(path.parent, ignore_errors=True)
    await callback.answer("Ma’lumotlar o‘chirildi")
    if isinstance(callback.message, Message):
        await callback.message.edit_text("Barcha ma’lumotlaringiz o‘chirildi.")
