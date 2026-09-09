import asyncio
import json
import logging
import shutil
import tempfile
from html import escape
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)
from aiogram.types import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards import (
    QUESTION_EXAMPLES,
    SKILL_SUGGESTION_VALUES,
    add_more_keyboard,
    cv_template_keyboard,
    delete_confirmation_keyboard,
    document_type_keyboard,
    edit_fields_keyboard,
    education_more_keyboard,
    language_keyboard,
    objective_education_level_keyboard,
    output_format_keyboard,
    photo_navigation_keyboard,
    portfolio_ready_keyboard,
    portfolio_review_keyboard,
    portfolio_sections_keyboard,
    portfolio_step_keyboard,
    portfolio_template_keyboard,
    portfolio_variant_keyboard,
    question_navigation_keyboard,
    relative_label,
    relative_more_keyboard,
    relatives_keyboard,
    remove_section_keyboard,
    review_keyboard,
    section_cancel_keyboard,
    start_keyboard,
    suggested_skill_codes,
)
from app.core.config import get_settings
from app.db.models import ResumeDraft, User
from app.documents.generator import DocumentGenerator
from app.repositories.resumes import (
    append_list_answer,
    continue_after_list,
    create_resume,
    delete_user_data,
    get_current_resume,
    get_or_create_user,
    get_user_document_paths,
    mark_completed,
    move_to_step,
    remove_section,
    reopen_list_step,
    return_to_review,
    save_answer,
    save_custom_section_content,
    save_custom_section_title,
    save_document,
    save_photo,
    set_editing_step,
    set_user_language,
    skip_step,
    start_custom_section,
    update_draft_flow,
)
from app.services.ai import (
    AIProvider,
    AIProviderUnavailableError,
    AIResponseError,
    AssistantDecision,
    local_message_decision,
)
from app.services.localization import (
    PORTFOLIO_SECTION_LABELS,
    PORTFOLIO_SECTION_PROMPTS,
    normalize_language,
    step_prompt,
    text,
)
from app.services.portfolio import (
    PortfolioDeploymentError,
    deploy_to_netlify,
    portfolio_zip,
    render_portfolio,
)
from app.services.resume_flow import (
    STEP_BY_KEY,
    EmploymentEntry,
    build_preview,
    next_step,
    normalize_answer,
    normalize_employment_period,
    normalize_employment_workplace,
    parse_answer,
    parse_employment_entries,
    previous_step,
    split_preview,
    validate_answer,
)
from app.services.templates import TEMPLATE_CODES

logger = logging.getLogger(__name__)
router = Router(name="resume")


def _step_prompt_with_example(step_key: str, language: str) -> str:
    locale = normalize_language(language)
    prompt = step_prompt(step_key, locale).rstrip()
    example = QUESTION_EXAMPLES.get(step_key, {}).get(locale)
    if not example:
        return prompt
    label = {"uz": "Misol", "en": "Example", "ru": "Пример"}[locale]
    return f"{prompt}\n({label}: {example})"


async def _user(session: AsyncSession, telegram_user: TelegramUser) -> User:
    return await get_or_create_user(
        session,
        telegram_user_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        language_code=telegram_user.language_code,
    )


async def _send_step(
    message: Message, step_key: str, language: str, data: dict[str, object] | None = None
) -> None:
    if step_key == "objective_relatives":
        await message.answer(
            text("choose_relatives", language), reply_markup=relatives_keyboard([], language)
        )
        return
    if step_key == "objective_education_level":
        await message.answer(
            step_prompt(step_key, language),
            reply_markup=objective_education_level_keyboard(language),
        )
        return
    prompt = _step_prompt_with_example(step_key, language)
    markup = question_navigation_keyboard(step_key, language)
    await message.answer(prompt, reply_markup=markup)


async def _send_relative_selection(
    message: Message, data: dict[str, object], language: str
) -> None:
    raw_selected = data.get("objective_relative_types", [])
    selected = list(map(str, raw_selected)) if isinstance(raw_selected, list) else []
    await message.answer(
        text("choose_relatives", language),
        reply_markup=relatives_keyboard(selected, language),
    )


async def _send_relative_step(
    message: Message, step_key: str, relationship_code: str, language: str
) -> None:
    prompt = _step_prompt_with_example(step_key, language).format(
        relationship=relative_label(relationship_code, language)
    )
    await message.answer(
        prompt,
        reply_markup=question_navigation_keyboard(step_key, language),
    )


async def _advance_relative(
    message: Message,
    session: AsyncSession,
    draft: ResumeDraft,
    language: str,
    index: int,
) -> None:
    data = dict(draft.data)
    raw_types = data.get("objective_relative_types", [])
    relative_types = list(map(str, raw_types)) if isinstance(raw_types, list) else []
    if index >= len(relative_types):
        updated = await update_draft_flow(
            session,
            draft,
            remove_keys=("objective_relative_index", "objective_pending_relative"),
            status="review",
        )
        await _send_preview(message, updated.data, language)
        return
    relationship_code = relative_types[index]
    await update_draft_flow(
        session,
        draft,
        data_updates={
            "objective_relative_index": index,
            "objective_pending_relative": {"type": relationship_code},
        },
        status="collecting",
        current_step="objective_relative_name",
    )
    await _send_relative_step(message, "objective_relative_name", relationship_code, language)


async def _show_template_gallery(message: Message, language: str) -> None:
    # Remove a previously installed WebApp reply keyboard.  Older chats may
    # still have that persistent button. The current gallery is always inline,
    # so it must never resize Telegram's composer on Android/iOS/Desktop.
    cleanup = await message.answer("⌨️", reply_markup=ReplyKeyboardRemove())
    try:
        await cleanup.delete()
    except TelegramBadRequest:
        logger.debug("Legacy reply-keyboard cleanup message could not be deleted")
    await message.answer(
        text("template_gallery_intro", language),
        reply_markup=cv_template_keyboard(language),
    )


@router.message(CommandStart())
async def start(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    await _user(session, message.from_user)
    # Telegram keeps reply keyboards in old chats. Remove the legacy WebApp
    # keyboard before showing the language selector, including for users who
    # never open the CV gallery again.
    await message.answer("✅", reply_markup=ReplyKeyboardRemove())
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


@router.message(Command("stop"))
async def stop_command(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    user = await _user(session, message.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is not None and draft.status != "completed":
        await update_draft_flow(session, draft, status="cancelled")
    await message.answer(
        text("stopped", user.language_code),
        reply_markup=start_keyboard(user.language_code),
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
        await _show_template_gallery(callback.message, user.language_code)


@router.callback_query(F.data.startswith("template:"))
async def template_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    template_code = callback.data.rsplit(":", 1)[-1]
    legacy_codes = {"classic", "modern"}
    if template_code not in (*TEMPLATE_CODES, *legacy_codes):
        return
    user = await _user(session, callback.from_user)
    await create_resume(
        session,
        user.id,
        document_type="cv",
        template_code=template_code,
        awaiting_photo=True,
    )
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            text("send_cv_photo", user.language_code),
            reply_markup=photo_navigation_keyboard(user.language_code, "cv"),
        )


@router.callback_query(F.data.startswith("template-family:"))
async def template_family_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    family = callback.data.rsplit(":", 1)[-1]
    if family not in ("classic", "modern", "europass"):
        return
    user = await _user(session, callback.from_user)
    await callback.answer()
    if isinstance(callback.message, Message):
        preview_dir = Path(__file__).resolve().parents[1] / "assets" / "template_previews"  # noqa: ASYNC240
        await callback.message.answer(text("choose_template_variant", user.language_code))
        # Albums cannot have a separate inline keyboard for every image, so
        # send each preview as its own message with its own select button.
        for number in range(1, 4):
            preview_path = preview_dir / f"{family}_{number}.png"
            if not preview_path.exists():
                continue
            await callback.message.answer_photo(
                photo=FSInputFile(preview_path),
                caption=f"{family.title()} {number}",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text={"uz": "✅ Tanlash", "en": "✅ Select", "ru": "✅ Выбрать"}[
                                    normalize_language(user.language_code)
                                ],
                                callback_data=f"template:{family}_{number}",
                            )
                        ]
                    ]
                ),
            )


@router.message(F.web_app_data)
async def template_webapp_selection(message: Message, session: AsyncSession) -> None:
    if message.from_user is None or message.web_app_data is None:
        return
    try:
        payload = json.loads(message.web_app_data.data)
    except (json.JSONDecodeError, TypeError):
        return
    if payload.get("action") != "select_template":
        return
    template_code = str(payload.get("template_code", ""))
    if template_code not in TEMPLATE_CODES:
        return
    user = await _user(session, message.from_user)
    await create_resume(
        session,
        user.id,
        document_type="cv",
        template_code=template_code,
        awaiting_photo=True,
    )
    await message.answer(
        text("template_selected", user.language_code),
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        text("send_cv_photo", user.language_code),
        reply_markup=photo_navigation_keyboard(user.language_code, "cv"),
    )


@router.callback_query(F.data == "document:objective")
async def objective_type_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    await create_resume(session, user.id, document_type="objective", awaiting_photo=True)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            text("send_photo", user.language_code),
            reply_markup=photo_navigation_keyboard(user.language_code, "objective"),
        )


@router.callback_query(F.data == "photo:skip")
async def skip_cv_photo_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status != "awaiting_photo" or draft.data.get("document_type") != "cv":
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    draft = await update_draft_flow(
        session,
        draft,
        remove_keys=("photo_path",),
        status="collecting",
        current_step="full_name",
    )
    await callback.answer()
    if isinstance(callback.message, Message):
        await _send_step(callback.message, draft.current_step, user.language_code)


@router.callback_query(F.data == "portfolio-photo:skip")
async def skip_portfolio_photo_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if (
        draft is None
        or draft.status != "awaiting_photo"
        or draft.data.get("document_type") != "portfolio"
    ):
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    await update_draft_flow(
        session,
        draft,
        remove_keys=("photo_path",),
        status="portfolio_sections",
        current_step="portfolio_sections",
    )
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(
            text("portfolio_sections_intro", user.language_code),
            reply_markup=portfolio_sections_keyboard(user.language_code, []),
        )


@router.callback_query(F.data.in_({"document:recommendation", "document:portfolio"}))
async def coming_soon_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    if callback.data == "document:portfolio":
        await create_resume(session, user.id, document_type="portfolio")
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                text("portfolio_example", user.language_code),
            )
            await callback.message.answer(
                text("portfolio_ready_prompt", user.language_code),
                reply_markup=portfolio_ready_keyboard(
                    user.language_code, get_settings().portfolio_example_url.strip()
                ),
            )
        return
    await callback.answer(text("coming_soon", user.language_code), show_alert=True)


@router.callback_query(F.data.startswith("portfolio-ready:"))
async def portfolio_ready_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    if callback.data == "portfolio-ready:again":
        await callback.message.answer(
            text("portfolio_example", user.language_code),
            reply_markup=portfolio_ready_keyboard(
                user.language_code, get_settings().portfolio_example_url.strip()
            ),
        )
        return
    await callback.message.answer(
        text("portfolio_choose_template", user.language_code),
        reply_markup=portfolio_template_keyboard(user.language_code),
    )


@router.callback_query(F.data.startswith("portfolio-template:"))
async def portfolio_template_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    template_code = callback.data.rsplit(":", 1)[-1]
    if template_code.rsplit("_", 1)[0] not in {"minimal", "modern", "creative", "developer"}:
        return
    user = await _user(session, callback.from_user)
    draft = await create_resume(session, user.id, document_type="portfolio")
    await update_draft_flow(
        session,
        draft,
        data_updates={"portfolio_template": template_code.rsplit("_", 1)[0]},
        status="awaiting_photo",
        current_step="portfolio_sections",
    )
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            text("portfolio_photo_prompt", user.language_code),
            reply_markup=photo_navigation_keyboard(user.language_code, "portfolio"),
        )


@router.callback_query(F.data.startswith("portfolio-family:"))
async def portfolio_family_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    family = callback.data.rsplit(":", 1)[-1] if callback.data else ""
    if family not in {"minimal", "modern", "creative", "developer"}:
        return
    user = await _user(session, callback.from_user)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(
            text("portfolio_choose_variant", user.language_code),
            reply_markup=portfolio_variant_keyboard(family, user.language_code),
        )


_PORTFOLIO_SECTION_ORDER = (
    "profile",
    "about",
    "skills",
    "experience",
    "education",
    "projects",
    "certificates",
    "publications",
    "languages",
    "achievements",
    "links",
    "contact",
)


@router.callback_query(F.data.startswith("portfolio-section:"))
async def portfolio_section_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    section = callback.data.rsplit(":", 1)[-1]
    if section not in _PORTFOLIO_SECTION_ORDER:
        return
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.data.get("document_type") != "portfolio":
        await callback.answer(text("start_first", user.language_code), show_alert=True)
        return
    selected = [str(item) for item in draft.data.get("portfolio_selected_sections", [])]
    selected_set = set(selected)
    selected = [code for code in _PORTFOLIO_SECTION_ORDER if code in selected_set]
    selected_set = set(selected)
    if section in selected_set:
        selected_set.remove(section)
    else:
        selected_set.add(section)
    selected = [code for code in _PORTFOLIO_SECTION_ORDER if code in selected_set]
    draft = await update_draft_flow(
        session,
        draft,
        status="portfolio_sections",
        current_step="portfolio_sections",
        data_updates={"portfolio_selected_sections": selected},
    )
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(
            reply_markup=portfolio_sections_keyboard(user.language_code, selected)
        )


@router.callback_query(F.data == "portfolio:start")
async def portfolio_finish_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.data.get("document_type") != "portfolio":
        await callback.answer(text("start_first", user.language_code), show_alert=True)
        return
    selected = [str(item) for item in draft.data.get("portfolio_selected_sections", [])]
    selected_set = set(selected)
    selected = [code for code in _PORTFOLIO_SECTION_ORDER if code in selected_set]
    if not selected:
        await callback.answer(text("portfolio_select_section", user.language_code), show_alert=True)
        return
    section = selected[0]
    draft = await update_draft_flow(
        session,
        draft,
        status="collecting",
        current_step="portfolio_section",
        data_updates={"portfolio_active_section": section, "portfolio_section_index": 0},
    )
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            PORTFOLIO_SECTION_PROMPTS[normalize_language(user.language_code)][section],
            reply_markup=portfolio_step_keyboard(user.language_code),
        )


@router.callback_query(F.data.startswith("portfolio:back:"))
async def portfolio_back_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    target = callback.data.rsplit(":", 1)[-1] if callback.data else ""
    await callback.answer()
    if callback.message is None:
        return
    if target == "documents":
        await callback.message.answer(
            text("choose_document", user.language_code),
            reply_markup=document_type_keyboard(user.language_code),
        )
        return
    if target == "example":
        await callback.message.answer(text("portfolio_example", user.language_code))
        await callback.message.answer(
            text("portfolio_ready_prompt", user.language_code),
            reply_markup=portfolio_ready_keyboard(
                user.language_code, get_settings().portfolio_example_url.strip()
            ),
        )
        return
    if draft is None or draft.data.get("document_type") != "portfolio":
        await callback.message.answer(text("start_first", user.language_code))
        return
    if target == "templates":
        await update_draft_flow(
            session, draft, status="portfolio_sections", current_step="portfolio_template"
        )
        await callback.message.answer(
            text("portfolio_choose_template", user.language_code),
            reply_markup=portfolio_template_keyboard(user.language_code),
        )
        return
    if target == "review":
        await update_draft_flow(session, draft, status="review", current_step="portfolio_sections")
        if isinstance(callback.message, Message):
            await _send_preview(callback.message, draft.data, user.language_code)
        return
    if target == "last":
        selected_set = {str(item) for item in draft.data.get("portfolio_selected_sections", [])}
        selected = [code for code in _PORTFOLIO_SECTION_ORDER if code in selected_set]
        if not selected:
            return
        last_index = len(selected) - 1
        last_section = selected[last_index]
        await update_draft_flow(
            session,
            draft,
            status="collecting",
            current_step="portfolio_section",
            data_updates={
                "portfolio_active_section": last_section,
                "portfolio_section_index": last_index,
            },
        )
        await callback.message.answer(
            PORTFOLIO_SECTION_PROMPTS[normalize_language(user.language_code)][last_section],
            reply_markup=portfolio_step_keyboard(user.language_code),
        )
        return
    if target != "section":
        return
    selected_set = {str(item) for item in draft.data.get("portfolio_selected_sections", [])}
    selected = [code for code in _PORTFOLIO_SECTION_ORDER if code in selected_set]
    index = int(draft.data.get("portfolio_section_index", 0))
    if index <= 0:
        await update_draft_flow(
            session,
            draft,
            remove_keys=("portfolio_active_section",),
            status="portfolio_sections",
            current_step="portfolio_sections",
        )
        await callback.message.answer(
            text("portfolio_sections_intro", user.language_code),
            reply_markup=portfolio_sections_keyboard(user.language_code, selected),
        )
        return
    previous_index = index - 1
    previous_section = selected[previous_index]
    await update_draft_flow(
        session,
        draft,
        status="collecting",
        current_step="portfolio_section",
        data_updates={
            "portfolio_active_section": previous_section,
            "portfolio_section_index": previous_index,
        },
    )
    await callback.message.answer(
        PORTFOLIO_SECTION_PROMPTS[normalize_language(user.language_code)][previous_section],
        reply_markup=portfolio_step_keyboard(user.language_code),
    )


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
    await message.answer(
        chunks[-1],
        reply_markup=(
            portfolio_review_keyboard(language)
            if data.get("document_type") == "portfolio"
            else review_keyboard(language)
        ),
    )


async def _publish_portfolio(
    message: Message,
    session: AsyncSession,
    draft: ResumeDraft,
    language: str,
    site_suffix: str,
) -> None:
    """Publish with the bot's server token, or give the user a ready ZIP.

    A Netlify account is an optional owner-side integration, never a user
    requirement. This keeps the portfolio flow usable for every Telegram user.
    """
    document = render_portfolio(draft.data, language)
    server_token = get_settings().netlify_token.get_secret_value().strip()
    status_message = await message.answer(text("portfolio_deploying", language))
    try:
        if server_token:
            url = await deploy_to_netlify(document, server_token, f"hujjat-portfolio-{site_suffix}")
            await mark_completed(session, draft)
            await status_message.edit_text(text("portfolio_deployed", language, url=url))
            return
        await message.answer_document(
            BufferedInputFile(portfolio_zip(document), filename="portfolio.zip"),
            caption=text("portfolio_download_ready", language),
        )
        await mark_completed(session, draft)
        await status_message.delete()
    except PortfolioDeploymentError as error:
        logger.warning("Portfolio deployment failed: %s", error)
        await status_message.edit_text(text("portfolio_deploy_failed", language))


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
    await set_editing_step(session, draft, step.key, is_list=step.is_list)
    await callback.answer()
    if isinstance(callback.message, Message):
        await _send_step(callback.message, step.key, user.language_code)


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
    draft = await save_photo(session, draft, str(photo_path))
    await message.answer(text("photo_saved", user.language_code))
    if draft.data.get("document_type") == "portfolio":
        await update_draft_flow(
            session, draft, status="portfolio_sections", current_step="portfolio_sections"
        )
        await message.answer(
            text("portfolio_sections_intro", user.language_code),
            reply_markup=portfolio_sections_keyboard(user.language_code, []),
        )
        return
    await _send_step(message, draft.current_step, user.language_code)


@router.message(F.document)
async def collect_photo_document(message: Message, session: AsyncSession, bot: Bot) -> None:
    if message.from_user is None or message.document is None:
        return
    user = await _user(session, message.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status != "awaiting_photo":
        await message.answer(
            text("start_first", user.language_code),
            reply_markup=start_keyboard(user.language_code),
        )
        return
    mime_type = (message.document.mime_type or "").lower()
    suffix_by_mime = {"image/jpeg": ".jpg", "image/png": ".png"}
    suffix = suffix_by_mime.get(mime_type)
    if suffix is None:
        await message.answer(
            text("invalid_photo_format", user.language_code),
            reply_markup=photo_navigation_keyboard(
                user.language_code, str(draft.data.get("document_type", "cv"))
            ),
        )
        return
    photo_dir = get_settings().storage_dir / str(draft.id)
    photo_dir.mkdir(parents=True, exist_ok=True)
    photo_path = photo_dir / f"photo{suffix}"
    await bot.download(message.document, destination=photo_path)
    draft = await save_photo(session, draft, str(photo_path))
    await message.answer(text("photo_saved", user.language_code))
    if draft.data.get("document_type") == "portfolio":
        await update_draft_flow(
            session, draft, status="portfolio_sections", current_step="portfolio_sections"
        )
        await message.answer(
            text("portfolio_sections_intro", user.language_code),
            reply_markup=portfolio_sections_keyboard(user.language_code, []),
        )
        return
    await _send_step(message, draft.current_step, user.language_code)


@router.message(F.voice | F.audio)
async def collect_voice(
    message: Message,
    session: AsyncSession,
    bot: Bot,
    ai_provider: AIProvider,
) -> None:
    if message.from_user is None:
        return

    user = await _user(session, message.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is not None and draft.status == "awaiting_photo":
        document_type = str(draft.data.get("document_type", "cv"))
        await message.answer(
            text("photo_required", user.language_code),
            reply_markup=photo_navigation_keyboard(user.language_code, document_type),
        )
        return

    if draft is None or draft.status not in (
        "collecting",
        "confirming_list",
        "confirming_edit_list",
        "editing",
        "editing_list",
        "adding_section_title",
        "adding_section_content",
    ):
        await message.answer(
            text("start_first", user.language_code),
            reply_markup=start_keyboard(user.language_code),
        )
        return

    media = message.voice or message.audio
    if media is None:
        return
    if media.file_size and media.file_size > 20 * 1024 * 1024:
        await message.answer(text("voice_too_large", user.language_code))
        return

    step = STEP_BY_KEY.get(draft.current_step)
    question = step_prompt(step.key, user.language_code) if step else draft.current_step
    mime_type = media.mime_type or ("audio/ogg" if message.voice else "audio/mpeg")
    suffix = Path(getattr(media, "file_name", "") or "").suffix
    if not suffix:
        suffix = ".ogg" if message.voice else ".audio"

    await message.answer(text("voice_processing", user.language_code))
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        with tempfile.TemporaryDirectory(prefix="cvbot-voice-") as temp_dir:
            audio_path = Path(temp_dir) / f"answer{suffix}"
            await bot.download(media, destination=audio_path)
            answer = await ai_provider.transcribe(
                audio_path,
                mime_type=mime_type,
                language=user.language_code,
                question=question,
            )
    except AIProviderUnavailableError:
        await message.answer(text("voice_disabled", user.language_code))
        return
    except (AIResponseError, OSError, ValueError):
        logger.exception("Could not transcribe Telegram audio")
        await message.answer(text("voice_error", user.language_code))
        return
    except Exception:
        logger.exception("Unexpected Gemini transcription error")
        await message.answer(text("voice_error", user.language_code))
        return

    await message.answer(text("voice_transcribed", user.language_code, answer=escape(answer)))
    logger.info(
        "Voice transcribed: language=%s, chars=%d, current_step=%s",
        user.language_code,
        len(answer),
        draft.current_step,
    )
    await collect_text(message, session, ai_provider, answer=answer)


def _employment_entry_data(entry: EmploymentEntry) -> dict[str, str | None]:
    return {
        "period": entry.period,
        "workplace": entry.workplace,
        "position": entry.position,
    }


def _pending_employment_entries(data: dict[str, object]) -> list[EmploymentEntry]:
    raw_entries = data.get("pending_employment_entries", [])
    if not isinstance(raw_entries, list):
        return []
    entries: list[EmploymentEntry] = []
    for item in raw_entries:
        if not isinstance(item, dict):
            continue
        entries.append(
            EmploymentEntry(
                period=str(item["period"]) if item.get("period") else None,
                workplace=str(item["workplace"]) if item.get("workplace") else None,
                position=str(item["position"]) if item.get("position") else None,
            )
        )
    return entries


def _first_missing_employment_field(
    entries: list[EmploymentEntry],
) -> tuple[int, str] | None:
    for index, entry in enumerate(entries):
        for field in ("period", "workplace", "position"):
            if not getattr(entry, field):
                return index, field
    return None


def _employment_detail_question(
    entry: EmploymentEntry,
    index: int,
    field: str,
    language: str,
) -> str:
    locale = normalize_language(language)
    subject = entry.workplace or entry.period or f"{index + 1}-ish joy"
    questions = {
        "period": {
            "uz": f"{subject}da qaysi sanadan qaysi sanagacha ishlagansiz?",
            "en": f"What dates did you work at {subject}?",
            "ru": f"В какие даты вы работали в {subject}?",
        },
        "workplace": {
            "uz": f"{subject} davrida qaysi kompaniya yoki tashkilotda ishlagansiz?",
            "en": f"Which company or organization did you work for during {subject}?",
            "ru": f"В какой компании или организации вы работали в период {subject}?",
        },
        "position": {
            "uz": f"{subject}da qaysi lavozimda ishlagansiz?",
            "en": f"What position did you hold at {subject}?",
            "ru": f"На какой должности вы работали в {subject}?",
        },
    }
    return questions[field][locale]


async def _handle_employment_answer(
    message: Message,
    session: AsyncSession,
    draft: ResumeDraft,
    step_key: str,
    raw_answer: str,
    language: str,
) -> bool:
    entries = _pending_employment_entries(draft.data)
    editing = bool(draft.data.get("pending_employment_editing", False))
    if entries:
        missing = _first_missing_employment_field(entries)
        if missing is None:
            return False
        index, field = missing
        current = entries[index]
        value: str | None
        if field == "period":
            value = normalize_employment_period(raw_answer)
        elif field == "workplace":
            # Repair drafts created before generic da/de workplaces such as
            # maktabida were understood by the parser.
            reparsed = parse_employment_entries(current.position or "")
            repaired = reparsed[0] if reparsed else None
            if repaired and repaired.workplace and repaired.position:
                current = EmploymentEntry(
                    period=current.period,
                    workplace=repaired.workplace,
                    position=repaired.position,
                )
                entries[index] = current
                value = current.workplace
            else:
                parsed = parse_employment_entries(raw_answer)
                value = (
                    parsed[0].workplace
                    if parsed and parsed[0].workplace
                    else normalize_employment_workplace(raw_answer)
                )
        else:
            value = normalize_answer(STEP_BY_KEY["objective_position"], raw_answer)
        if not value:
            await message.answer(_employment_detail_question(current, index, field, language))
            return True
        entries[index] = EmploymentEntry(
            period=value if field == "period" else current.period,
            workplace=value if field == "workplace" else current.workplace,
            position=value if field == "position" else current.position,
        )
    else:
        normalized = normalize_answer(STEP_BY_KEY[step_key], raw_answer)
        if normalized == "-":
            return False
        entries = parse_employment_entries(raw_answer)
        if not entries:
            return False
        editing = draft.status in ("editing", "editing_list", "confirming_edit_list")

    missing = _first_missing_employment_field(entries)
    if missing is not None:
        await update_draft_flow(
            session,
            draft,
            data_updates={
                "pending_employment_entries": [_employment_entry_data(entry) for entry in entries],
                "pending_employment_editing": editing,
            },
            status="collecting",
            current_step=step_key,
        )
        index, field = missing
        await message.answer(_employment_detail_question(entries[index], index, field, language))
        return True

    await update_draft_flow(
        session,
        draft,
        remove_keys=("pending_employment_entries", "pending_employment_editing"),
    )
    await append_list_answer(
        session,
        draft,
        key=step_key,
        values=[entry.render() for entry in entries],
        editing=editing,
    )
    await message.answer(
        text("add_more_question", language),
        reply_markup=add_more_keyboard(language),
    )
    return True


@router.message(F.text & ~F.text.startswith("/"))
async def collect_text(
    message: Message,
    session: AsyncSession,
    ai_provider: AIProvider,
    answer: str | None = None,
) -> None:
    raw_answer = answer if answer is not None else message.text
    if message.from_user is None or raw_answer is None:
        return
    user = await _user(session, message.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is not None and draft.status == "portfolio_token":
        token = raw_answer.strip()
        try:
            await message.delete()
        except TelegramBadRequest:
            logger.warning("Could not delete the one-time Netlify token message")
        site_name = f"hujjat-portfolio-{message.from_user.id}"
        status_message = await message.answer(text("portfolio_deploying", user.language_code))
        try:
            url = await deploy_to_netlify(
                render_portfolio(draft.data, user.language_code), token, site_name
            )
            await mark_completed(session, draft)
            await status_message.edit_text(text("portfolio_deployed", user.language_code, url=url))
        except PortfolioDeploymentError as error:
            logger.warning("Portfolio deployment failed: %s", error)
            await status_message.edit_text(text("portfolio_deploy_failed", user.language_code))
        return
    if (
        draft is not None
        and draft.status == "collecting"
        and draft.current_step == "portfolio_section"
    ):
        section = str(draft.data.get("portfolio_active_section", ""))
        if not section:
            return
        updates: dict[str, object] = {}
        lines = [line.strip() for line in raw_answer.splitlines() if line.strip()]
        if section == "profile":
            updates = {"full_name": lines[0] if lines else raw_answer.strip()}
            if len(lines) > 1:
                updates["job_title"] = lines[1]
            if len(lines) > 2:
                updates["portfolio_tagline"] = " ".join(lines[2:])
        elif section == "about":
            updates = {"summary": raw_answer.strip()}
        elif section == "skills":
            updates = {"skills": [item.strip() for item in raw_answer.split(",") if item.strip()]}
        elif section in {"experience", "education", "languages"}:
            updates = {section: lines}
        elif section == "contact":
            updates = {"email": lines[0] if lines else raw_answer.strip()}
            if len(lines) > 1:
                updates["phone"] = lines[1]
            if len(lines) > 2:
                updates["location"] = lines[2]
        else:
            custom = list(draft.data.get("portfolio_sections", []))
            custom = [
                item for item in custom if not isinstance(item, dict) or item.get("key") != section
            ]
            locale = normalize_language(user.language_code)
            custom.append(
                {
                    "key": section,
                    "title": PORTFOLIO_SECTION_LABELS[locale][section],
                    "content": raw_answer.strip(),
                }
            )
            updates = {"portfolio_sections": custom}
        selected = [str(item) for item in draft.data.get("portfolio_selected_sections", [])]
        selected_set = set(selected)
        selected = [code for code in _PORTFOLIO_SECTION_ORDER if code in selected_set]
        index = int(draft.data.get("portfolio_section_index", 0)) + 1
        if index < len(selected):
            next_section = selected[index]
            draft = await update_draft_flow(
                session,
                draft,
                data_updates={
                    **updates,
                    "portfolio_active_section": next_section,
                    "portfolio_section_index": index,
                },
                status="collecting",
                current_step="portfolio_section",
            )
            prompt = PORTFOLIO_SECTION_PROMPTS[normalize_language(user.language_code)][next_section]
            await message.answer(
                text("portfolio_section_saved", user.language_code, prompt=prompt),
                reply_markup=portfolio_step_keyboard(user.language_code),
            )
        else:
            draft = await update_draft_flow(
                session,
                draft,
                data_updates=updates,
                remove_keys=("portfolio_active_section",),
                status="review",
                current_step="portfolio_sections",
            )
            await _send_preview(message, draft.data, user.language_code)
        return
    step = STEP_BY_KEY.get(draft.current_step) if draft is not None else None
    current_question = step_prompt(step.key, user.language_code) if step else None
    # Do not spend a Gemini request (or wait for its timeout) for ordinary
    # answers inside an active form.  The current step already defines what
    # this message means; Gemini is reserved for commands and free-form chat.
    decision = local_message_decision(raw_answer)
    active_form = (
        draft is not None
        and draft.status
        in {
            "collecting",
            "confirming_list",
            "confirming_edit_list",
            "editing",
            "editing_list",
        }
        and step is not None
    )
    if decision is None and active_form:
        decision = AssistantDecision(intent="form_answer", answer_value=raw_answer)
    elif decision is None and draft is not None and draft.status == "awaiting_photo":
        decision = None
    elif decision is None:
        try:
            decision = await ai_provider.understand_message(
                raw_answer,
                language=user.language_code,
                current_question=current_question,
                current_step=step.key if step else None,
            )
        except AIProviderUnavailableError:
            decision = None
        except Exception:
            logger.exception("Could not understand user message with Gemini")
            decision = None

    if decision is not None:
        logger.info(
            "Message intent: intent=%s, current_step=%s, answer_chars=%d",
            decision.intent,
            draft.current_step if draft is not None else None,
            len(decision.answer_value or ""),
        )

    if decision is not None:
        if decision.intent == "show_last_document":
            await _show_last(message, session, message.from_user)
            return
        if decision.intent == "start_new":
            command_text = raw_answer.casefold().replace("’", "'")
            if any(word in command_text for word in ("cv", "rezyume", "resume")):
                await _show_template_gallery(message, user.language_code)
                return
            await message.answer(
                text("choose_document", user.language_code),
                reply_markup=document_type_keyboard(user.language_code),
            )
            return
        if decision.intent == "stop":
            if draft is not None and draft.status != "completed":
                await update_draft_flow(session, draft, status="cancelled")
            await message.answer(
                text("stopped", user.language_code),
                reply_markup=start_keyboard(user.language_code),
            )
            return
        if decision.intent == "help":
            await message.answer(text("help", user.language_code))
            return
        if decision.intent == "go_back":
            if draft is not None:
                document_type = str(draft.data.get("document_type", "cv"))
                preceding = previous_step(draft.current_step, document_type)
                if preceding is not None:
                    await move_to_step(session, draft, preceding.key)
                    await _send_step(message, preceding.key, user.language_code, draft.data)
                    return
            await message.answer(text("start_first", user.language_code))
            return
        if decision.intent == "skip":
            if draft is None or step is None:
                await message.answer(text("start_first", user.language_code))
                return
            document_type = str(draft.data.get("document_type", "cv"))
            following = next_step(step.key, document_type)
            if draft.status in ("confirming_list", "confirming_edit_list"):
                draft = await continue_after_list(
                    session,
                    draft,
                    following.key if following else None,
                )
            else:
                if "pending_employment_entries" in draft.data:
                    draft = await update_draft_flow(
                        session,
                        draft,
                        remove_keys=(
                            "pending_employment_entries",
                            "pending_employment_editing",
                        ),
                    )
                draft = await skip_step(
                    session,
                    draft,
                    key=step.key,
                    next_step_key=following.key if following else None,
                )
            if draft.status == "review" or following is None:
                await _send_preview(message, draft.data, user.language_code)
            elif following.key == "objective_relatives":
                await _send_relative_selection(message, draft.data, user.language_code)
            else:
                await _send_step(message, following.key, user.language_code, draft.data)
            return
        if decision.intent == "chat":
            reply = decision.reply or text("help", user.language_code)
            await message.answer(escape(reply))
            if draft is not None and step is not None:
                await _send_step(message, step.key, user.language_code, draft.data)
            return
        if decision.answer_value:
            raw_answer = decision.answer_value.strip()

    if draft is not None and draft.status == "awaiting_photo":
        document_type = str(draft.data.get("document_type", "cv"))
        await message.answer(
            text("photo_required", user.language_code),
            reply_markup=photo_navigation_keyboard(user.language_code, document_type),
        )
        return
    if draft is not None and draft.status == "adding_section_title":
        if len(raw_answer.strip()) > 80:
            await message.answer(text("long_answer", user.language_code))
            return
        await save_custom_section_title(session, draft, raw_answer.strip())
        await message.answer(
            text("section_content_prompt", user.language_code),
            reply_markup=section_cancel_keyboard(user.language_code),
        )
        return
    if draft is not None and draft.status == "adding_section_content":
        if len(raw_answer.strip()) > 600:
            await message.answer(text("long_answer", user.language_code))
            return
        draft = await save_custom_section_content(session, draft, raw_answer.strip())
        await _send_preview(message, draft.data, user.language_code)
        return
    if draft is None or draft.status not in (
        "collecting",
        "confirming_list",
        "confirming_edit_list",
        "editing",
        "editing_list",
    ):
        await message.answer(
            text("start_first", user.language_code),
            reply_markup=start_keyboard(user.language_code),
        )
        return

    step = STEP_BY_KEY.get(draft.current_step)
    if step is None:
        await message.answer(text("broken_state", user.language_code))
        return
    if step.key == "objective_relatives":
        await _send_relative_selection(message, draft.data, user.language_code)
        return
    if step.key == "objective_education_level":
        await message.answer(
            text("choose_education_button", user.language_code),
            reply_markup=objective_education_level_keyboard(user.language_code),
        )
        return

    if step.key in {"objective_employment", "experience"}:
        if await _handle_employment_answer(
            message,
            session,
            draft,
            step.key,
            raw_answer,
            user.language_code,
        ):
            return

    raw_answer = normalize_answer(step, raw_answer)
    validation_error = validate_answer(step, raw_answer, user.language_code)
    if validation_error:
        await message.answer(validation_error)
        return

    if step.key == "objective_specialty" and draft.status == "collecting":
        data = dict(draft.data)
        raw_entries = data.get("objective_educations", [])
        entries = list(raw_entries) if isinstance(raw_entries, list) else []
        entries.append(
            {
                "level": str(data.get("objective_education_level", "")),
                "institution": str(data.get("objective_graduated", "")),
                "specialty": raw_answer.strip(),
            }
        )
        await update_draft_flow(
            session,
            draft,
            data_updates={
                "objective_educations": entries,
                "objective_education_level": str(data.get("objective_education_level", "")),
                "objective_graduated": "\n".join(str(item["institution"]) for item in entries),
                "objective_specialty": "\n".join(str(item["specialty"]) for item in entries),
            },
            status="confirming_education",
            current_step="objective_specialty",
        )
        await message.answer(
            text("education_saved", user.language_code),
            reply_markup=education_more_keyboard(user.language_code),
        )
        return

    relative_fields = {
        "objective_relative_name": "name",
        "objective_relative_birth": "birth",
        "objective_relative_work": "work",
        "objective_relative_address": "address",
    }
    if step.key in relative_fields:
        data = dict(draft.data)
        raw_pending = data.get("objective_pending_relative", {})
        pending = dict(raw_pending) if isinstance(raw_pending, dict) else {}
        pending[relative_fields[step.key]] = raw_answer.strip()
        relationship_code = str(pending.get("type", ""))
        next_relative_steps = {
            "objective_relative_name": "objective_relative_birth",
            "objective_relative_birth": "objective_relative_work",
            "objective_relative_work": "objective_relative_address",
        }
        next_relative_step = next_relative_steps.get(step.key)
        if next_relative_step:
            await update_draft_flow(
                session,
                draft,
                data_updates={"objective_pending_relative": pending},
                status="collecting",
                current_step=next_relative_step,
            )
            await _send_relative_step(
                message, next_relative_step, relationship_code, user.language_code
            )
            return

        raw_relatives = data.get("objective_relatives", [])
        relatives = list(raw_relatives) if isinstance(raw_relatives, list) else []
        relatives.append(
            " | ".join(
                [
                    relative_label(relationship_code, user.language_code),
                    str(pending.get("name", "")),
                    str(pending.get("birth", "")),
                    str(pending.get("work", "")),
                    str(pending.get("address", "")),
                ]
            )
        )
        sibling_types = {"older_brother", "younger_brother", "older_sister", "younger_sister"}
        draft = await update_draft_flow(
            session,
            draft,
            data_updates={"objective_relatives": relatives},
            remove_keys=("objective_pending_relative",),
            status="confirming_relative" if relationship_code in sibling_types else "collecting",
        )
        if relationship_code in sibling_types:
            await message.answer(
                text("relative_saved_more", user.language_code),
                reply_markup=relative_more_keyboard(user.language_code),
            )
        else:
            await _advance_relative(
                message,
                session,
                draft,
                user.language_code,
                int(data.get("objective_relative_index", 0)) + 1,
            )
        return

    was_editing = draft.status in ("editing", "editing_list", "confirming_edit_list")
    document_type = str(draft.data.get("document_type", "cv"))
    following_step = None if was_editing else next_step(step.key, document_type)
    parsed_value = parse_answer(step, raw_answer)
    if (
        document_type == "objective"
        and step.optional
        and raw_answer.strip() == "-"
        and not step.is_list
    ):
        parsed_value = {
            "uz": "yo‘q",
            "en": "none",
            "ru": "нет",
        }[normalize_language(user.language_code)]

    if step.is_list and isinstance(parsed_value, list) and parsed_value:
        await append_list_answer(
            session,
            draft,
            key=step.key,
            values=parsed_value,
            editing=was_editing,
        )
        await message.answer(
            text("add_more_question", user.language_code),
            reply_markup=add_more_keyboard(user.language_code),
        )
        return

    draft = await save_answer(
        session,
        draft,
        key=step.key,
        value=parsed_value,
        next_step_key=following_step.key if following_step else None,
    )

    if draft.status == "review":
        await _send_preview(message, draft.data, user.language_code)
    elif following_step:
        await _send_step(message, following_step.key, user.language_code, draft.data)


@router.callback_query(F.data.startswith("example:"))
async def example_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    await callback.answer(
        {
            "uz": "Misoldagi formatda yozing.",
            "en": "Use the format shown in the example.",
            "ru": "Используйте формат из примера.",
        }[normalize_language(user.language_code)],
        show_alert=True,
    )


@router.callback_query(F.data.startswith("skill:suggest:"))
async def skill_suggestion_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.current_step != "skills" or draft.status != "collecting":
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    code = callback.data.rsplit(":", 1)[-1]
    job_title = str(draft.data.get("job_title", ""))
    if code not in suggested_skill_codes(job_title) or code not in SKILL_SUGGESTION_VALUES:
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    await append_list_answer(
        session,
        draft,
        key="skills",
        values=[SKILL_SUGGESTION_VALUES[code]],
        editing=False,
    )
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(
            text("add_more_question", user.language_code),
            reply_markup=add_more_keyboard(user.language_code),
        )


@router.callback_query(F.data.startswith("objective-education:"))
async def objective_education_level_callback(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    if callback.data is None:
        return
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if (
        draft is None
        or draft.status != "collecting"
        or draft.current_step != "objective_education_level"
    ):
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    code = callback.data.rsplit(":", 1)[-1]
    locale = normalize_language(user.language_code)
    values = {
        "uz": {
            "higher": "oliy",
            "incomplete_higher": "tugallanmagan oliy",
            "secondary_special": "o‘rta maxsus",
            "secondary": "o‘rta",
        },
        "en": {
            "higher": "higher education",
            "incomplete_higher": "incomplete higher education",
            "secondary_special": "specialized secondary education",
            "secondary": "secondary education",
        },
        "ru": {
            "higher": "высшее",
            "incomplete_higher": "незаконченное высшее",
            "secondary_special": "среднее специальное",
            "secondary": "среднее",
        },
    }
    value = values[locale].get(code)
    if value is None:
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    await save_answer(
        session,
        draft,
        key="objective_education_level",
        value=value,
        next_step_key="objective_graduated",
    )
    await callback.answer()
    if isinstance(callback.message, Message):
        await _send_step(callback.message, "objective_graduated", user.language_code)


@router.callback_query(F.data == "education:add")
async def add_education_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status != "confirming_education":
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    await update_draft_flow(
        session,
        draft,
        remove_keys=("objective_graduated", "objective_specialty"),
        status="collecting",
        current_step="objective_graduated",
    )
    await callback.answer()
    if isinstance(callback.message, Message):
        await _send_step(callback.message, "objective_graduated", user.language_code)


@router.callback_query(F.data == "education:done")
async def finish_education_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status != "confirming_education":
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    await update_draft_flow(session, draft, status="collecting", current_step="objective_degree")
    await callback.answer()
    if isinstance(callback.message, Message):
        await _send_step(callback.message, "objective_degree", user.language_code)


@router.callback_query(F.data.startswith("relative:toggle:"))
async def toggle_relative_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.current_step != "objective_relatives":
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    code = callback.data.rsplit(":", 1)[-1]
    raw_selected = draft.data.get("objective_relative_types", [])
    selected = list(map(str, raw_selected)) if isinstance(raw_selected, list) else []
    if code in selected:
        selected.remove(code)
    else:
        selected.append(code)
    await update_draft_flow(
        session,
        draft,
        data_updates={"objective_relative_types": selected},
        status="selecting_relatives",
        current_step="objective_relatives",
    )
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(
            reply_markup=relatives_keyboard(selected, user.language_code)
        )


@router.callback_query(F.data == "relative:types:none")
async def no_relatives_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.current_step != "objective_relatives":
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    draft = await update_draft_flow(
        session,
        draft,
        remove_keys=("objective_relative_types", "objective_relatives"),
        status="review",
    )
    await callback.answer()
    if isinstance(callback.message, Message):
        await _send_preview(callback.message, draft.data, user.language_code)


@router.callback_query(F.data == "relative:types:done")
async def finish_relative_types_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.current_step != "objective_relatives":
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    selected = draft.data.get("objective_relative_types", [])
    if not isinstance(selected, list) or not selected:
        await callback.answer(
            text("choose_at_least_one_relative", user.language_code), show_alert=True
        )
        return
    await callback.answer()
    if isinstance(callback.message, Message):
        await _advance_relative(callback.message, session, draft, user.language_code, 0)


@router.callback_query(F.data.in_({"relative:add_same", "relative:next"}))
async def relative_more_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status != "confirming_relative":
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    index = int(draft.data.get("objective_relative_index", 0))
    if callback.data == "relative:add_same":
        next_index = index
    else:
        next_index = index + 1
    await callback.answer()
    if isinstance(callback.message, Message):
        await _advance_relative(callback.message, session, draft, user.language_code, next_index)


@router.callback_query(F.data == "list:add")
async def add_list_item_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status not in ("confirming_list", "confirming_edit_list"):
        await callback.answer(text("broken_state", user.language_code), show_alert=True)
        return
    step = STEP_BY_KEY.get(draft.current_step)
    if step is None:
        await callback.answer(text("broken_state", user.language_code), show_alert=True)
        return
    editing = draft.status == "confirming_edit_list"
    await reopen_list_step(session, draft, editing=editing)
    await callback.answer()
    if isinstance(callback.message, Message):
        await _send_step(callback.message, step.key, user.language_code, draft.data)


@router.callback_query(F.data == "list:done")
async def finish_list_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None or draft.status not in ("confirming_list", "confirming_edit_list"):
        await callback.answer(text("broken_state", user.language_code), show_alert=True)
        return
    editing = draft.status == "confirming_edit_list"
    document_type = str(draft.data.get("document_type", "cv"))
    following_step = None if editing else next_step(draft.current_step, document_type)
    if editing:
        draft = await return_to_review(session, draft)
    else:
        draft = await continue_after_list(
            session, draft, following_step.key if following_step else None
        )
    await callback.answer()
    if isinstance(callback.message, Message):
        if following_step:
            if following_step.key == "objective_relatives":
                await _send_relative_selection(callback.message, draft.data, user.language_code)
            else:
                await _send_step(callback.message, following_step.key, user.language_code)
        else:
            await _send_preview(callback.message, draft.data, user.language_code)


@router.callback_query(F.data.startswith("flow:back"))
async def flow_back_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None:
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    requested_step = callback.data.rsplit(":", 1)[-1] if callback.data else ""
    if requested_step not in ("back", draft.current_step):
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    if draft.status in ("editing", "editing_list", "confirming_edit_list"):
        draft = await return_to_review(session, draft)
        await callback.answer()
        if isinstance(callback.message, Message):
            await _send_preview(callback.message, draft.data, user.language_code)
        return

    if draft.status == "confirming_education":
        raw_entries = draft.data.get("objective_educations", [])
        entries = list(raw_entries) if isinstance(raw_entries, list) else []
        last = entries.pop() if entries else {}
        await update_draft_flow(
            session,
            draft,
            data_updates={
                "objective_educations": entries,
                "objective_education_level": str(last.get("level", "")),
                "objective_graduated": str(last.get("institution", "")),
            },
            remove_keys=("objective_specialty",),
            status="collecting",
            current_step="objective_specialty",
        )
        await callback.answer()
        if isinstance(callback.message, Message):
            await _send_step(callback.message, "objective_specialty", user.language_code)
        return

    if draft.status == "confirming_relative":
        data = dict(draft.data)
        raw_relatives = data.get("objective_relatives", [])
        relatives = list(raw_relatives) if isinstance(raw_relatives, list) else []
        parts = [part.strip() for part in str(relatives.pop()).split("|")] if relatives else []
        raw_types = data.get("objective_relative_types", [])
        types = list(map(str, raw_types)) if isinstance(raw_types, list) else []
        index = int(data.get("objective_relative_index", 0))
        relationship_code = types[index] if index < len(types) else ""
        pending = {
            "type": relationship_code,
            "name": parts[1] if len(parts) > 1 else "",
            "birth": parts[2] if len(parts) > 2 else "",
            "work": parts[3] if len(parts) > 3 else "",
        }
        await update_draft_flow(
            session,
            draft,
            data_updates={
                "objective_relatives": relatives,
                "objective_pending_relative": pending,
            },
            status="collecting",
            current_step="objective_relative_address",
        )
        await callback.answer()
        if isinstance(callback.message, Message):
            await _send_relative_step(
                callback.message,
                "objective_relative_address",
                relationship_code,
                user.language_code,
            )
        return

    relative_previous = {
        "objective_relative_name": "objective_relatives",
        "objective_relative_birth": "objective_relative_name",
        "objective_relative_work": "objective_relative_birth",
        "objective_relative_address": "objective_relative_work",
    }
    if draft.current_step in relative_previous:
        target_step = relative_previous[draft.current_step]
        await callback.answer()
        if not isinstance(callback.message, Message):
            return
        if target_step == "objective_relatives":
            await update_draft_flow(
                session,
                draft,
                remove_keys=("objective_relative_index", "objective_pending_relative"),
                status="selecting_relatives",
                current_step="objective_relatives",
            )
            await _send_relative_selection(callback.message, draft.data, user.language_code)
            return
        raw_pending = draft.data.get("objective_pending_relative", {})
        pending = dict(raw_pending) if isinstance(raw_pending, dict) else {}
        relationship_code = str(pending.get("type", ""))
        await update_draft_flow(session, draft, status="collecting", current_step=target_step)
        await _send_relative_step(
            callback.message, target_step, relationship_code, user.language_code
        )
        return

    document_type = str(draft.data.get("document_type", "cv"))
    preceding_step = previous_step(draft.current_step, document_type)
    await callback.answer()
    if not isinstance(callback.message, Message):
        return
    if preceding_step:
        await move_to_step(session, draft, preceding_step.key)
        await _send_step(callback.message, preceding_step.key, user.language_code)
    elif document_type == "cv":
        await _show_template_gallery(callback.message, user.language_code)
    else:
        await callback.message.answer(
            text("choose_document", user.language_code),
            reply_markup=document_type_keyboard(user.language_code),
        )


@router.callback_query(F.data.startswith("flow:skip:"))
async def flow_skip_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    if callback.data is None:
        return
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    requested_step = callback.data.rsplit(":", 1)[-1]
    requested_step_definition = STEP_BY_KEY.get(requested_step)
    if (
        draft is None
        or requested_step != draft.current_step
        or requested_step_definition is None
        or not requested_step_definition.optional
        or draft.status not in ("collecting", "editing", "editing_list")
    ):
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    document_type = str(draft.data.get("document_type", "cv"))
    following_step = next_step(draft.current_step, document_type)
    draft = await skip_step(
        session,
        draft,
        key=requested_step,
        next_step_key=following_step.key if following_step else None,
    )
    await callback.answer()
    if isinstance(callback.message, Message):
        if draft.status == "review":
            await _send_preview(callback.message, draft.data, user.language_code)
        elif following_step:
            await _send_step(callback.message, following_step.key, user.language_code)


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
        await callback.message.answer(
            text("section_title_prompt", user.language_code),
            reply_markup=section_cancel_keyboard(user.language_code),
        )


@router.callback_query(F.data == "section:cancel")
async def cancel_section_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    user = await _user(session, callback.from_user)
    draft = await get_current_resume(session, user.id)
    if draft is None:
        await callback.answer(text("old_button", user.language_code), show_alert=True)
        return
    draft = await return_to_review(session, draft)
    await callback.answer()
    if isinstance(callback.message, Message):
        await _send_preview(callback.message, draft.data, user.language_code)


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
    if not isinstance(callback.message, Message):
        return
    if draft.data.get("document_type") == "portfolio":
        # Publishing uses the owner-configured server token. The end user
        # should never be asked to register at Netlify or share credentials.
        await _publish_portfolio(
            callback.message,
            session,
            draft,
            user.language_code,
            str(callback.from_user.id),
        )
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
