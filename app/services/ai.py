import asyncio
from pathlib import Path
from typing import Literal, Protocol

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.services.resume_schema import ResumeData

AssistantIntent = Literal[
    "form_answer",
    "show_last_document",
    "start_new",
    "stop",
    "help",
    "go_back",
    "skip",
    "chat",
]


class AssistantDecision(BaseModel):
    intent: AssistantIntent
    answer_value: str | None = Field(
        default=None,
        description="Only the value needed by the current form question.",
    )
    reply: str | None = Field(
        default=None,
        description="Short answer in the user's language for chat intent.",
    )


class AIProvider(Protocol):
    async def transcribe(
        self,
        audio_path: Path,
        *,
        mime_type: str,
        language: str,
        question: str,
    ) -> str: ...

    async def extract_resume(self, text: str) -> ResumeData: ...

    async def understand_message(
        self,
        message: str,
        *,
        language: str,
        current_question: str | None,
        current_step: str | None,
    ) -> AssistantDecision: ...

    async def aclose(self) -> None: ...


class AIProviderUnavailableError(RuntimeError):
    """Raised when an AI-backed operation is not configured."""


class AIResponseError(RuntimeError):
    """Raised when Gemini returns no usable response."""


class GeminiProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        router_model: str = "gemini-3.5-flash-lite",
        voice_model: str = "gemini-3.5-transcribe",
    ) -> None:
        self._model = model
        self._router_model = router_model
        self._voice_model = voice_model
        self._client = genai.Client(api_key=api_key)

    async def transcribe(
        self,
        audio_path: Path,
        *,
        mime_type: str,
        language: str,
        question: str,
    ) -> str:
        del question
        language_codes = {
            "uz": ["uz-UZ"],
            "en": ["en-US"],
            "ru": ["ru-RU"],
        }.get(language, [])
        uploaded_file = None
        try:
            async with asyncio.timeout(30):
                uploaded_file = await asyncio.to_thread(
                    self._client.files.upload,
                    file=audio_path,
                    config=types.UploadFileConfig(mime_type=mime_type),
                )
                if not uploaded_file.uri:
                    raise AIResponseError("Gemini audio upload returned no URI")
                interaction = await self._client.aio.interactions.create(
                    model=self._voice_model,
                    input=[
                        {
                            "type": "audio",
                            "uri": uploaded_file.uri,
                            "mime_type": uploaded_file.mime_type or mime_type,
                        }
                    ],
                    generation_config={
                        "transcription_config": {
                            "language_codes": language_codes,
                            "custom_vocabulary": [
                                "HujjatAI",
                                "rezyume",
                                "obyektivka",
                                "tavsiyanoma",
                                "portfolio",
                                "Europass",
                            ],
                            "mode": "smart",
                        }
                    },
                )
        finally:
            if uploaded_file is not None and uploaded_file.name:
                await asyncio.to_thread(
                    self._client.files.delete,
                    name=uploaded_file.name,
                )
        answer = str(getattr(interaction, "output_text", "") or "").strip()
        if not answer:
            raise AIResponseError("Gemini returned an empty transcription")
        return answer

    async def extract_resume(self, text: str) -> ResumeData:
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=(
                "Extract resume data from the text. Do not invent missing information.\n\n"
                f"{text}"
            ),
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_schema=ResumeData,
            ),
        )
        payload = response.text or ""
        if not payload:
            raise AIResponseError("Gemini returned an empty resume response")
        return ResumeData.model_validate_json(payload)

    async def understand_message(
        self,
        message: str,
        *,
        language: str,
        current_question: str | None,
        current_step: str | None,
    ) -> AssistantDecision:
        normalized = " ".join(message.casefold().replace("’", "'").split())
        if normalized in {
            "salom",
            "assalomu alaykum",
            "assalom alaykum",
            "hello",
            "hi",
            "hey",
            "rahmat",
            "katta rahmat",
            "thanks",
            "спасибо",
        }:
            return AssistantDecision(intent="chat", reply="Salom! Sizga qanday yordam beray?")
        local_patterns: tuple[tuple[AssistantIntent, tuple[str, ...]], ...] = (
            (
                "show_last_document",
                (
                    "oxirgi cv",
                    "cv'imni chiqar",
                    "cvimni chiqar",
                    "oxirgi hujjat",
                    "last cv",
                    "latest cv",
                    "последнее резюме",
                ),
            ),
            (
                "start_new",
                (
                    "yangi cv",
                    "yangi hujjat",
                    "cv yarat",
                    "cv tayyorlamoqchiman",
                    "cv tayyorla",
                    "cv qilmoqchiman",
                    "cv tuzmoqchiman",
                    "cv yasamoqchiman",
                    "cv kerak",
                    "rezyume tayyorlamoqchiman",
                    "rezyume kerak",
                    "resume tayyorlamoqchiman",
                    "resume kerak",
                    "obyektivka yarat",
                    "new cv",
                    "create cv",
                    "новое резюме",
                ),
            ),
            ("stop", ("to'xtat", "bekor qil", "stop", "cancel", "останови", "отмени")),
            ("help", ("yordam", "nima qila olasan", "help", "помощь", "что ты умеешь")),
            (
                "go_back",
                ("orqaga", "oldingi savol", "go back", "previous", "назад"),
            ),
            (
                "skip",
                (
                    "keyingi savol",
                    "keyingisiga o't",
                    "keyingisiga ot",
                    "buni tashlab o't",
                    "buni tashlab ot",
                    "o'tkazib yubor",
                    "otkazib yubor",
                    "skip this",
                    "next question",
                    "пропусти",
                ),
            ),
        )
        for intent, patterns in local_patterns:
            if any(pattern in normalized for pattern in patterns):
                return AssistantDecision(intent=intent)

        prompt = f"""
You are the intent router for HujjatAI, a Telegram bot that creates CVs and
obyektivka documents. Classify the user's message and never invent personal data.

Bot language: {language}
Current form step: {current_step or "none"}
Current question: {current_question or "none"}
User message: {message}

Rules:
- form_answer: the message answers the current question. Put only the requested
  value in answer_value, removing conversational filler but preserving facts.
  For objective_party, return only the party name, or "-" when the user says
  they are not a member (for example "partiyaga a'zo emasman").
  For objective_employment and experience, convert conversational speech to
  "start – end | workplace | position". Example: "Big IT kompaniyasida 2025
  yil martdan 2025 yil sentabrgacha Project Manager bo'lib ishlaganman" becomes
  "2025-yil mart – 2025-yil sentabr | Big IT kompaniyasi | Project Manager".
- show_last_document: asks to show or resend their previous/last CV or document.
- start_new: asks to create a new CV, resume, obyektivka, or document.
- stop: asks to cancel or stop the current process.
- help: asks how the bot works or what it can do.
- go_back: asks to return to the previous question.
- skip: asks to skip the current question or move to the next one without saving
  the spoken command as an answer.
- chat: greetings, thanks, unrelated questions, or anything that must not be
  stored as form data. Reply briefly and helpfully in the bot language. If a
  form question is active, remind the user what answer is expected.
""".strip()
        async with asyncio.timeout(20):
            response = await self._client.aio.models.generate_content(
                model=self._router_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=300,
                    response_mime_type="application/json",
                    response_schema=AssistantDecision,
                    thinking_config=types.ThinkingConfig(thinking_level="minimal"),
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )
        payload = response.text or ""
        if not payload:
            raise AIResponseError("Gemini returned an empty intent response")
        return AssistantDecision.model_validate_json(payload)

    async def aclose(self) -> None:
        await self._client.aio.aclose()


class DisabledAIProvider:
    """Fallback that keeps typed answers available without an API key."""

    async def transcribe(
        self,
        audio_path: Path,
        *,
        mime_type: str,
        language: str,
        question: str,
    ) -> str:
        del audio_path, mime_type, language, question
        raise AIProviderUnavailableError("GEMINI_API_KEY is not configured")

    async def extract_resume(self, text: str) -> ResumeData:
        del text
        raise AIProviderUnavailableError("GEMINI_API_KEY is not configured")

    async def understand_message(
        self,
        message: str,
        *,
        language: str,
        current_question: str | None,
        current_step: str | None,
    ) -> AssistantDecision:
        del message, language, current_question, current_step
        raise AIProviderUnavailableError("GEMINI_API_KEY is not configured")

    async def aclose(self) -> None:
        return None
