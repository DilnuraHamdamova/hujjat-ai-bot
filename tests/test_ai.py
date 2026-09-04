import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.bot.handlers import collect_voice
from app.services.ai import (
    AIProviderUnavailableError,
    AssistantDecision,
    DisabledAIProvider,
    GeminiProvider,
)


class FakeModels:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    async def generate_content(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(text=self.responses.pop(0))


class FakeFiles:
    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.uploads: list[dict[str, object]] = []

    def upload(self, **kwargs: object) -> SimpleNamespace:
        self.uploads.append(kwargs)
        return SimpleNamespace(
            name="files/test-audio",
            uri="https://example.test/audio",
            mime_type="audio/ogg",
        )

    def delete(self, *, name: str) -> None:
        self.deleted.append(name)


class FakeInteractions:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(output_text=self.responses.pop(0))


class FakeClient:
    def __init__(self, responses: list[str]) -> None:
        self.models = FakeModels(responses)
        self.files = FakeFiles()
        self.interactions = FakeInteractions(responses)
        self.aio = SimpleNamespace(models=self.models, interactions=self.interactions)


@pytest.mark.asyncio
async def test_gemini_transcribes_audio_with_form_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = FakeClient(["Ali Valiyev"])
    monkeypatch.setattr("app.services.ai.genai.Client", lambda **_: fake_client)
    audio_path = tmp_path / "answer.ogg"
    audio_path.write_bytes(b"fake-ogg")

    provider = GeminiProvider(
        "test-key",
        "gemini-text-test",
        voice_model="gemini-voice-test",
    )
    answer = await provider.transcribe(
        audio_path,
        mime_type="audio/ogg",
        language="uz",
        question="Ism va familiyangizni kiriting",
    )

    assert answer == "Ali Valiyev"
    assert fake_client.files.uploads[0]["config"].mime_type == "audio/ogg"
    call = fake_client.interactions.calls[0]
    assert call["model"] == "gemini-voice-test"
    assert call["generation_config"] == {
        "transcription_config": {
            "language_codes": ["uz-UZ"],
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
    }
    assert fake_client.files.deleted == ["files/test-audio"]


@pytest.mark.asyncio
async def test_gemini_extracts_typed_resume_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = FakeClient(
        [
            '{"full_name":"Ali Valiyev","skills":["Python"],'
            '"experience":[],"education":[],"languages":[]}'
        ]
    )
    monkeypatch.setattr("app.services.ai.genai.Client", lambda **_: fake_client)

    provider = GeminiProvider("test-key", "gemini-test")
    resume = await provider.extract_resume("Ali Valiyev Python dasturchi")

    assert resume.full_name == "Ali Valiyev"
    assert resume.skills == ["Python"]


@pytest.mark.asyncio
async def test_gemini_classifies_commands_without_saving_them_as_form_answers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = FakeClient(
        ['{"intent":"show_last_document","answer_value":null,"reply":null}']
    )
    monkeypatch.setattr("app.services.ai.genai.Client", lambda **_: fake_client)

    provider = GeminiProvider("test-key", "gemini-test")
    decision = await provider.understand_message(
        "Oxirgi CV'imni chiqarib ber",
        language="uz",
        current_question="Ism va familiyangizni kiriting",
        current_step="full_name",
    )

    assert decision == AssistantDecision(intent="show_last_document")
    assert fake_client.models.calls == []


@pytest.mark.asyncio
async def test_gemini_classifies_spoken_skip_without_an_api_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = FakeClient([])
    monkeypatch.setattr("app.services.ai.genai.Client", lambda **_: fake_client)

    provider = GeminiProvider("test-key", "gemini-test")
    decision = await provider.understand_message(
        "Buni tashlab o'tib, keyingi savolga o't",
        language="uz",
        current_question="Tug'ilgan joyingizni kiriting",
        current_step="objective_birth_place",
    )

    assert decision == AssistantDecision(intent="skip")
    assert fake_client.models.calls == []


@pytest.mark.asyncio
async def test_greeting_is_not_saved_as_a_form_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = FakeClient([])
    monkeypatch.setattr("app.services.ai.genai.Client", lambda **_: fake_client)

    provider = GeminiProvider("test-key", "gemini-test")
    decision = await provider.understand_message(
        "salom",
        language="uz",
        current_question="Ism va familiyangizni kiriting",
        current_step="full_name",
    )

    assert decision.intent == "chat"
    assert fake_client.models.calls == []


@pytest.mark.asyncio
async def test_cv_creation_phrase_is_local_start_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = FakeClient([])
    monkeypatch.setattr("app.services.ai.genai.Client", lambda **_: fake_client)

    provider = GeminiProvider("test-key", "gemini-test")
    decision = await provider.understand_message(
        "CV tayyorlamoqchiman",
        language="uz",
        current_question="Hozirgi lavozimingizni kiriting",
        current_step="objective_position",
    )

    assert decision == AssistantDecision(intent="start_new")
    assert fake_client.models.calls == []


@pytest.mark.asyncio
async def test_gemini_uses_fast_router_for_non_local_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = FakeClient(
        ['{"intent":"form_answer","answer_value":"Ali Valiyev","reply":null}']
    )
    monkeypatch.setattr("app.services.ai.genai.Client", lambda **_: fake_client)

    provider = GeminiProvider(
        "test-key",
        "gemini-document-test",
        router_model="gemini-router-test",
    )
    decision = await provider.understand_message(
        "Mening ismim Ali Valiyev",
        language="uz",
        current_question="Ism va familiyangizni kiriting",
        current_step="full_name",
    )

    assert decision == AssistantDecision(
        intent="form_answer",
        answer_value="Ali Valiyev",
    )
    assert fake_client.models.calls[0]["model"] == "gemini-router-test"


@pytest.mark.asyncio
async def test_disabled_provider_keeps_voice_failure_explicit(tmp_path: Path) -> None:
    with pytest.raises(AIProviderUnavailableError):
        await DisabledAIProvider().transcribe(
            tmp_path / "missing.ogg",
            mime_type="audio/ogg",
            language="uz",
            question="Savol",
        )

class FakeMessage:
    def __init__(self) -> None:
        self.from_user = SimpleNamespace(id=1)
        self.chat = SimpleNamespace(id=10)
        self.voice = SimpleNamespace(file_size=100, mime_type="audio/ogg")
        self.audio = None
        self.answers: list[str] = []

    async def answer(self, value: str, **_: object) -> None:
        self.answers.append(value)


class FakeBot:
    async def send_chat_action(self, *_: object) -> None:
        pass

    async def download(self, _: object, destination: Path) -> None:
        await asyncio.to_thread(destination.write_bytes, b"fake audio")


class FakeProvider:
    async def transcribe(self, *_: object, **__: object) -> str:
        return "Ali Valiyev"


@pytest.mark.asyncio
async def test_voice_answer_is_forwarded_to_the_text_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = FakeMessage()
    received: list[str] = []

    async def fake_user(*_: object) -> SimpleNamespace:
        return SimpleNamespace(id=1, language_code="uz")

    async def fake_draft(*_: object) -> SimpleNamespace:
        return SimpleNamespace(status="collecting", current_step="full_name", data={})

    async def fake_collect_text(
        _: object,
        __: object,
        ___: object,
        answer: str | None = None,
    ) -> None:
        if answer is not None:
            received.append(answer)

    monkeypatch.setattr("app.bot.handlers._user", fake_user)
    monkeypatch.setattr("app.bot.handlers.get_current_resume", fake_draft)
    monkeypatch.setattr("app.bot.handlers.collect_text", fake_collect_text)

    await collect_voice(message, object(), FakeBot(), FakeProvider())

    assert received == ["Ali Valiyev"]
    assert any("Ali Valiyev" in answer for answer in message.answers)
