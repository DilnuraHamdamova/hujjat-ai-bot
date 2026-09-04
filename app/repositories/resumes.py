from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, ResumeDraft, User


async def get_or_create_user(
    session: AsyncSession,
    *,
    telegram_user_id: int,
    username: str | None,
    first_name: str | None,
    language_code: str | None,
) -> User:
    user = await session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))
    if user is None:
        user = User(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            language_code=language_code or "uz",
        )
        session.add(user)
    else:
        user.username = username
        user.first_name = first_name
    await session.commit()
    await session.refresh(user)
    return user


async def set_user_language(session: AsyncSession, user: User, language_code: str) -> User:
    user.language_code = language_code
    await session.commit()
    await session.refresh(user)
    return user


async def create_resume(
    session: AsyncSession,
    user_id: UUID,
    *,
    document_type: str = "cv",
    template_code: str = "classic",
    awaiting_photo: bool = False,
) -> ResumeDraft:
    existing = await session.scalars(
        select(ResumeDraft).where(
            ResumeDraft.user_id == user_id,
            ResumeDraft.status.in_(
                (
                    "awaiting_photo",
                    "collecting",
                    "confirming_list",
                    "confirming_edit_list",
                    "confirming_education",
                    "selecting_relatives",
                    "confirming_relative",
                    "editing",
                    "editing_list",
                    "review",
                    "adding_section_title",
                    "adding_section_content",
                    "portfolio_token",
                )
            ),
        )
    )
    for draft in existing:
        draft.status = "cancelled"

    first_step = "objective_full_name" if document_type == "objective" else "full_name"
    draft = ResumeDraft(
        user_id=user_id,
        status="awaiting_photo" if awaiting_photo else "collecting",
        current_step=first_step,
        template_code=template_code,
        data={"document_type": document_type},
    )
    session.add(draft)
    await session.commit()
    await session.refresh(draft)
    return draft


async def get_current_resume(session: AsyncSession, user_id: UUID) -> ResumeDraft | None:
    draft = await session.scalar(
        select(ResumeDraft)
        .where(
            ResumeDraft.user_id == user_id,
            ResumeDraft.status.in_(
                (
                    "awaiting_photo",
                    "collecting",
                    "confirming_list",
                    "confirming_edit_list",
                    "confirming_education",
                    "selecting_relatives",
                    "confirming_relative",
                    "editing",
                    "editing_list",
                    "review",
                    "adding_section_title",
                    "adding_section_content",
                    "portfolio_token",
                    "completed",
                )
            ),
        )
        .order_by(ResumeDraft.created_at.desc())
        .limit(1)
    )
    return draft


async def save_answer(
    session: AsyncSession,
    draft: ResumeDraft,
    *,
    key: str,
    value: Any,
    next_step_key: str | None,
) -> ResumeDraft:
    data = dict(draft.data)
    data[key] = value
    draft.data = data
    draft.version += 1

    if draft.status in ("editing", "editing_list"):
        draft.status = "review"
    elif next_step_key is None:
        draft.status = "review"
    else:
        draft.current_step = next_step_key

    await session.commit()
    await session.refresh(draft)
    return draft


async def append_list_answer(
    session: AsyncSession,
    draft: ResumeDraft,
    *,
    key: str,
    values: list[str],
    editing: bool = False,
) -> ResumeDraft:
    data = dict(draft.data)
    current = data.get(key, [])
    items = list(current) if isinstance(current, list) else []
    items.extend(values)
    data[key] = items
    draft.data = data
    draft.status = "confirming_edit_list" if editing else "confirming_list"
    draft.current_step = key
    draft.version += 1
    await session.commit()
    await session.refresh(draft)
    return draft


async def update_draft_flow(
    session: AsyncSession,
    draft: ResumeDraft,
    *,
    data_updates: dict[str, Any] | None = None,
    remove_keys: tuple[str, ...] = (),
    status: str | None = None,
    current_step: str | None = None,
) -> ResumeDraft:
    data = dict(draft.data)
    for key in remove_keys:
        data.pop(key, None)
    if data_updates:
        data.update(data_updates)
    draft.data = data
    if status is not None:
        draft.status = status
    if current_step is not None:
        draft.current_step = current_step
    draft.version += 1
    await session.commit()
    await session.refresh(draft)
    return draft


async def continue_after_list(
    session: AsyncSession, draft: ResumeDraft, next_step_key: str | None
) -> ResumeDraft:
    if next_step_key is None:
        draft.status = "review"
    else:
        draft.status = "collecting"
        draft.current_step = next_step_key
    await session.commit()
    await session.refresh(draft)
    return draft


async def reopen_list_step(
    session: AsyncSession, draft: ResumeDraft, *, editing: bool = False
) -> ResumeDraft:
    draft.status = "editing_list" if editing else "collecting"
    await session.commit()
    await session.refresh(draft)
    return draft


async def set_editing_step(
    session: AsyncSession, draft: ResumeDraft, step_key: str, *, is_list: bool = False
) -> ResumeDraft:
    draft.status = "editing_list" if is_list else "editing"
    draft.current_step = step_key
    await session.commit()
    await session.refresh(draft)
    return draft


async def save_photo(session: AsyncSession, draft: ResumeDraft, photo_path: str) -> ResumeDraft:
    data = dict(draft.data)
    data["photo_path"] = photo_path
    draft.data = data
    draft.status = "collecting"
    draft.current_step = (
        "objective_full_name" if data.get("document_type") == "objective" else "full_name"
    )
    await session.commit()
    await session.refresh(draft)
    return draft


async def move_to_step(session: AsyncSession, draft: ResumeDraft, step_key: str) -> ResumeDraft:
    draft.status = "collecting"
    draft.current_step = step_key
    await session.commit()
    await session.refresh(draft)
    return draft


async def skip_step(
    session: AsyncSession,
    draft: ResumeDraft,
    *,
    key: str,
    next_step_key: str | None,
) -> ResumeDraft:
    data = dict(draft.data)
    data.pop(key, None)
    draft.data = data
    if draft.status in ("editing", "editing_list"):
        draft.status = "review"
    elif next_step_key is None:
        draft.status = "review"
    else:
        draft.status = "collecting"
        draft.current_step = next_step_key
    draft.version += 1
    await session.commit()
    await session.refresh(draft)
    return draft


async def return_to_review(session: AsyncSession, draft: ResumeDraft) -> ResumeDraft:
    draft.status = "review"
    await session.commit()
    await session.refresh(draft)
    return draft


async def start_custom_section(session: AsyncSession, draft: ResumeDraft) -> ResumeDraft:
    draft.status = "adding_section_title"
    await session.commit()
    await session.refresh(draft)
    return draft


async def save_custom_section_title(
    session: AsyncSession, draft: ResumeDraft, title: str
) -> ResumeDraft:
    data = dict(draft.data)
    data["pending_section_title"] = title
    draft.data = data
    draft.status = "adding_section_content"
    await session.commit()
    await session.refresh(draft)
    return draft


async def save_custom_section_content(
    session: AsyncSession, draft: ResumeDraft, content: str
) -> ResumeDraft:
    data = dict(draft.data)
    title = str(data.pop("pending_section_title", ""))
    raw_sections = data.get("custom_sections", [])
    sections = list(raw_sections) if isinstance(raw_sections, list) else []
    sections.append({"title": title, "content": content})
    data["custom_sections"] = sections
    draft.data = data
    draft.status = "review"
    draft.version += 1
    await session.commit()
    await session.refresh(draft)
    return draft


async def remove_section(
    session: AsyncSession, draft: ResumeDraft, section_key: str
) -> ResumeDraft:
    data = dict(draft.data)
    if section_key.startswith("custom_"):
        raw_sections = data.get("custom_sections", [])
        sections = list(raw_sections) if isinstance(raw_sections, list) else []
        try:
            sections.pop(int(section_key.removeprefix("custom_")))
        except (ValueError, IndexError):
            pass
        data["custom_sections"] = sections
    else:
        data.pop(section_key, None)
    draft.data = data
    draft.status = "review"
    draft.version += 1
    await session.commit()
    await session.refresh(draft)
    return draft


async def mark_completed(session: AsyncSession, draft: ResumeDraft) -> None:
    draft.status = "completed"
    await session.commit()


async def save_document(
    session: AsyncSession,
    *,
    resume_id: UUID,
    file_format: str,
    storage_key: str,
    checksum: str,
) -> Document:
    document = await session.scalar(
        select(Document).where(
            Document.resume_id == resume_id,
            Document.format == file_format,
        )
    )
    if document is None:
        document = Document(
            resume_id=resume_id,
            format=file_format,
            storage_key=storage_key,
            checksum=checksum,
        )
        session.add(document)
    else:
        document.storage_key = storage_key
        document.checksum = checksum
    await session.commit()
    await session.refresh(document)
    return document


async def delete_user_data(session: AsyncSession, telegram_user_id: int) -> None:
    await session.execute(delete(User).where(User.telegram_user_id == telegram_user_id))
    await session.commit()


async def get_user_document_paths(session: AsyncSession, telegram_user_id: int) -> list[str]:
    result = await session.scalars(
        select(Document.storage_key)
        .join(ResumeDraft, Document.resume_id == ResumeDraft.id)
        .join(User, ResumeDraft.user_id == User.id)
        .where(User.telegram_user_id == telegram_user_id)
    )
    return list(result)
