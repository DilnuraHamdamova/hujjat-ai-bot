from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    language_code: Mapped[str] = mapped_column(String(8), default="uz")

    resumes: Mapped[list[ResumeDraft]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ResumeDraft(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_drafts"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="collecting", index=True)
    current_step: Mapped[str] = mapped_column(String(64), default="full_name")
    template_code: Mapped[str] = mapped_column(String(32), default="classic")
    data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)

    user: Mapped[User] = relationship(back_populates="resumes")
    documents: Mapped[list[Document]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resume_drafts.id", ondelete="CASCADE"), index=True
    )
    format: Mapped[str] = mapped_column(String(8))
    storage_key: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(String(64))

    resume: Mapped[ResumeDraft] = relationship(back_populates="documents")

    __table_args__ = (UniqueConstraint("resume_id", "format"),)


class ProcessedUpdate(TimestampMixin, Base):
    __tablename__ = "processed_updates"

    update_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
