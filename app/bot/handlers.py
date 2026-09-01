import asyncio
import logging
import shutil
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.types import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import (
    cv_template_keyboard,
    delete_confirmation_keyboard,
    document_type_keyboard,
    edit_fields_keyboard,
    language_keyboard,
    output_format_keyboard,
    remove_section_keyboard,
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
    remove_section,
    save_answer,
    save_custom_section_content,
    save_custom_section_title,
    save_document,
    save_photo,
    set_editing_step,
    set_user_language,
    start_custom_section,
)
from app.services.localization import normalize_language, step_prompt, text
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
        "<b>Assalomu alaykum! Hujjat tayyorlab beruvchi botga xush kelibsiz!</b>\n\n"
        + text("choose_language", "uz"),
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data.startswith("language:"))
async def language_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    language = normalize_language(callback.data.rsplit(":", 1)[-1])
    user = await _user(session, callback.from_user)
    await set_user_language(session, user, language)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            f"{text('welcome', language)}\n\n<b>{text('choose_document', language)}</b>",
            reply_markup=document_type_keyboard(language),
        )


@router.message(Command("help"))
async def help_command(message: Message, session: AsyncSession) -> None:
    if message.from_user:
        user = await _user(session, message.from_user)
        await message.answer(text("help", user.language_code))


@router.message(Command("new"))
async def new_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user = await _user(session, message.from_user)
    await message.answer(
        text("choose_document", user.language_code),
        reply_markup=document_type_keyboard(user.language_code),
    )


@router.callback_query(F.data == "resume:new")
async def new_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            text("choose_document", user.language_code),
            reply_markup=document_type_keyboard(user.language_code),
        )


@router.callback_query(F.data == "document:choose")
async def document_choose_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text("choose_document", user.language_code),
            reply_markup=document_type_keyboard(user.language_code),
        )


@router.callback_query(F.data == "document:cv")
async def cv_type_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            text("choose_template", user.language_code),
            reply_markup=cv_template_keyboard(user.language_code),
        )


@router.callback_query(F.data.startswith("template:"))
async def template_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    template_code = callback.data.rsplit(":", 1)[-1]
    if template_code not in ("classic", "modern", "europass"):
        return
    user = await _user(session, callback.from_user)
    await create_resume(session, user.id, document_type="cv", template_code=template_code)
    await callback.answer()
    if callback.message:
        await callback.message.answer(step_prompt(STEPS[0].key, user.language_code))


@router.callback_query(F.data == "document:objective")
async def objective_type_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    await create_resume(session, user.id, document_type="objective", awaiting_photo=True)
    await callback.answer()
    if callback.message:
        await callback.message.answer(text("send_photo", user.language_code))


@router.callback_query(F.data.in_({"document:recommendation", "document:portfolio"}))
async def coming_soon_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    await callback.answer(text("coming_soon", user.language_code), show_alert=True)


async def _show_last(message: Message, session: AsyncSession, telegram_user: TelegramUser) -> None:
    user = await _user(session, telegram_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or not draft.data:
        await message.answer(
            text("no_cv", user.language_code),
            reply_markup=start_keyboard(user.language_code),
        )
        return
    await _send_preview(message, draft.data, user.language_code)


async def _send_preview(message: Message, data: dict[str, object], language: str) -> None:
    chunks = split_preview(build_preview(data, language))
    for chunk in chunks[:-1]:
        await message.answer(chunk)
    await message.answer(chunks[-1], reply_markup=review_keyboard(language))


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
async def edit_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    await callback.answer()
    if callback.message and draft:
        document_type = str(draft.data.get("document_type", "cv"))
        await callback.message.answer(
            text("which_edit", user.language_code),
            reply_markup=edit_fields_keyboard(user.language_code, document_type),
        )


@router.callback_query(F.data.startswith("resume:field:"))
async def edit_field_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    step_key = callback.data.rsplit(":", 1)[-1]
    step = STEP_BY_KEY.get(step_key)
    user = await _user(session, callback.from_user)
    if step is None:
        await callback.answer(text("invalid_field", user.language_code), show_alert=True)
        return
    draft = await get_current_resume(session, user.id)
    if draft is None:
        await callback.answer(text("cv_not_found", user.language_code), show_alert=True)
        return
    await set_editing_step(session, draft, step.key)
    await callback.answer()
    if callback.message:
        await callback.message.answer(step_prompt(step.key, user.language_code))


@router.message(F.photo)
async def collect_photo(message: Message, session: AsyncSession, bot: Bot) -> None:
    if message.from_user is None or not message.photo:
        return
    user = await _user(session, message.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status != "awaiting_photo":
        await message.answer(
            text("start_first", user.language_code),
            reply_markup=start_keyboard(user.language_code),
        )
        return
    photo_dir = get_settings().storage_dir / str(draft.id)
    photo_dir.mkdir(parents=True, exist_ok=True)
    photo_path = photo_dir / "photo.jpg"
    await bot.download(message.photo[-1], destination=photo_path)
    await save_photo(session, draft, str(photo_path))
    await message.answer(text("photo_saved", user.language_code))
    await message.answer(step_prompt("objective_full_name", user.language_code))


@router.message(F.voice | F.audio)
async def voice_not_enabled(message: Message, session: AsyncSession) -> None:
    if message.from_user:
        user = await _user(session, message.from_user)
        await message.answer(text("voice_disabled", user.language_code))


@router.message(F.text & ~F.text.startswith("/"))
async def collect_text(message: Message, session: AsyncSession) -> None:
    if message.from_user is None or message.text is None:
        return
    user = await _user(session, message.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is not None and draft.status == "awaiting_photo":
        await message.answer(text("photo_required", user.language_code))
        return
    if draft is not None and draft.status == "adding_section_title":
        if len(message.text.strip()) > 80:
            await message.answer(text("long_answer", user.language_code))
            return
        await save_custom_section_title(session, draft, message.text.strip())
        await message.answer(text("section_content_prompt", user.language_code))
        return
    if draft is not None and draft.status == "adding_section_content":
        if len(message.text.strip()) > 600:
            await message.answer(text("long_answer", user.language_code))
            return
        draft = await save_custom_section_content(session, draft, message.text.strip())
        await _send_preview(message, draft.data, user.language_code)
        return
    if draft is None or draft.status not in ("collecting", "editing"):
        await message.answer(
            text("start_first", user.language_code),
            reply_markup=start_keyboard(user.language_code),
        )
        return

    step = STEP_BY_KEY.get(draft.current_step)
    if step is None:
        await message.answer(text("broken_state", user.language_code))
        return

    validation_error = validate_answer(step, message.text, user.language_code)
    if validation_error:
        await message.answer(validation_error)
        return

    was_editing = draft.status == "editing"
    document_type = str(draft.data.get("document_type", "cv"))
    following_step = None if was_editing else next_step(step.key, document_type)
    draft = await save_answer(
        session,
        draft,
        key=step.key,
        value=parse_answer(step, message.text),
        next_step_key=following_step.key if following_step else None,
    )

    if draft.status == "review":
        await _send_preview(message, draft.data, user.language_code)
    elif following_step:
        await message.answer(step_prompt(following_step.key, user.language_code))


@router.callback_query(F.data == "section:add")
async def add_section_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None:
        await callback.answer(text("cv_not_found", user.language_code), show_alert=True)
        return
    await start_custom_section(session, draft)
    await callback.answer()
    if callback.message:
        await callback.message.answer(text("section_title_prompt", user.language_code))


@router.callback_query(F.data == "section:remove")
async def remove_section_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None:
        await callback.answer(text("cv_not_found", user.language_code), show_alert=True)
        return
    keyboard = remove_section_keyboard(draft.data, user.language_code)
    if not keyboard.inline_keyboard:
        await callback.answer(text("no_removable_sections", user.language_code), show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            text("choose_remove_section", user.language_code), reply_markup=keyboard
        )


@router.callback_query(F.data.startswith("section:delete:"))
async def delete_section_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None:
        await callback.answer(text("cv_not_found", user.language_code), show_alert=True)
        return
    section_key = callback.data.split(":", 2)[-1]
    draft = await remove_section(session, draft, section_key)
    await callback.answer(text("section_removed", user.language_code))
    if isinstance(callback.message, Message):
        await _send_preview(callback.message, draft.data, user.language_code)


@router.callback_query(F.data == "resume:approve")
async def approve_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status not in ("review", "completed"):
        await callback.answer(text("approve_missing", user.language_code), show_alert=True)
        return

    await callback.answer()
    if callback.message is None:
        return
    await callback.message.answer(
        text("choose_format", user.language_code), reply_markup=output_format_keyboard()
    )


@router.callback_query(F.data.startswith("format:"))
async def format_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    file_format = callback.data.rsplit(":", 1)[-1]
    if file_format not in ("pdf", "docx"):
        return
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status not in ("review", "completed"):
        await callback.answer(text("approve_missing", user.language_code), show_alert=True)
        return
    await callback.answer(text("preparing_alert", user.language_code))
    if callback.message is None:
        return
    format_name = "PDF" if file_format == "pdf" else "Word"
    status_message = await callback.message.answer(
        text("preparing", user.language_code, format=format_name)
    )
    try:
        generator = DocumentGenerator(get_settings().storage_dir)
        artifacts = await asyncio.to_thread(
            generator.generate,
            draft.id,
            draft.data,
            user.language_code,
            draft.template_code,
            file_format,
        )
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
            basename = "Obyektivka" if draft.data.get("document_type") == "objective" else "CV"
            filename = f"{basename}.{artifact.format}"
            await callback.message.answer_document(
                FSInputFile(artifact.path, filename=filename),
                caption=text("file_ready", user.language_code, filename=filename),
            )
        await status_message.edit_text(text("success", user.language_code))
    except Exception:
        logger.exception("Document generation failed", extra={"resume_id": str(draft.id)})
        await status_message.edit_text(text("generation_error", user.language_code))


@router.message(Command("delete_me"))
async def delete_me_command(message: Message, session: AsyncSession) -> None:
    if message.from_user:
        user = await _user(session, message.from_user)
        await message.answer(
            text("delete_prompt", user.language_code),
            reply_markup=delete_confirmation_keyboard(user.language_code),
        )


@router.callback_query(F.data == "privacy:cancel")
async def delete_cancel(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    await callback.answer(text("cancelled", user.language_code))
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text("data_kept", user.language_code))


@router.callback_query(F.data == "privacy:delete")
async def delete_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    language = user.language_code
    paths = await get_user_document_paths(session, callback.from_user.id)
    await delete_user_data(session, callback.from_user.id)
    for raw_path in paths:
        path = Path(raw_path)
        if path.parent.exists():
            shutil.rmtree(path.parent, ignore_errors=True)
    await callback.answer(text("data_deleted_alert", language))
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text("data_deleted", language))
