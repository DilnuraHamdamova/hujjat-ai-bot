from typing import Any

from pydantic import BaseModel, Field, field_validator


class ResumeData(BaseModel):
    full_name: str | None = None
    job_title: str | None = None
    phone: str | None = None
    email: str | None = None
    location: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)

    @field_validator("skills", "experience", "education", "languages", mode="before")
    @classmethod
    def normalize_lists(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return [str(item).strip() for item in value if str(item).strip()]
