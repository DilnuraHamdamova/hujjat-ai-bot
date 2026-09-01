from pathlib import Path
from typing import Protocol

from app.services.resume_schema import ResumeData


class AIProvider(Protocol):
    async def transcribe(self, audio_path: Path) -> str: ...

    async def extract_resume(self, text: str) -> ResumeData: ...


class DisabledAIProvider:
    """Text-only MVP provider. Replace with OpenAIProvider without changing handlers."""

    async def transcribe(self, audio_path: Path) -> str:
        del audio_path
        raise RuntimeError("Ovozli xabarlar hali yoqilmagan.")

    async def extract_resume(self, text: str) -> ResumeData:
        del text
        raise RuntimeError("Erkin matndan AI orqali ajratish hali yoqilmagan.")
