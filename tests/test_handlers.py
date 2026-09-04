from types import SimpleNamespace

import pytest

from app.bot.handlers import _handle_employment_answer


class FakeMessage:
    def __init__(self) -> None:
        self.answers: list[str] = []

    async def answer(self, value: str, **_: object) -> None:
        self.answers.append(value)


@pytest.mark.asyncio
async def test_multiple_employments_request_and_fill_missing_position(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    message = FakeMessage()
    draft = SimpleNamespace(data={}, status="collecting", current_step="objective_employment")
    saved_values: list[str] = []

    async def fake_update(
        _: object,
        current_draft: SimpleNamespace,
        *,
        data_updates: dict[str, object] | None = None,
        remove_keys: tuple[str, ...] = (),
        status: str | None = None,
        current_step: str | None = None,
    ) -> SimpleNamespace:
        data = dict(current_draft.data)
        for key in remove_keys:
            data.pop(key, None)
        if data_updates:
            data.update(data_updates)
        current_draft.data = data
        if status:
            current_draft.status = status
        if current_step:
            current_draft.current_step = current_step
        return current_draft

    async def fake_append(
        _: object,
        __: object,
        *,
        key: str,
        values: list[str],
        editing: bool,
    ) -> None:
        assert key == "objective_employment"
        assert editing is False
        saved_values.extend(values)

    monkeypatch.setattr("app.bot.handlers.update_draft_flow", fake_update)
    monkeypatch.setattr("app.bot.handlers.append_list_answer", fake_append)

    handled = await _handle_employment_answer(
        message,
        object(),
        draft,
        "objective_employment",
        (
            "Perfect Consulting kompaniyasida 2025-yil martdan 2025-yil "
            "sentabrgacha ishlaganman, 2026-yil yanvardan maygacha Innovatsion "
            "rivojlanish agentligida dasturchi bolib, 2026-yil apreldan "
            "hozirgacha dasturchi bolib Big IT kompaniyasida ishlaganman"
        ),
        "uz",
    )

    assert handled is True
    assert message.answers == [
        "Perfect Consulting kompaniyasida qaysi lavozimda ishlagansiz?"
    ]
    assert saved_values == []

    await _handle_employment_answer(
        message,
        object(),
        draft,
        "objective_employment",
        "Proyekt manager bo'lib ishlaganman",
        "uz",
    )

    assert saved_values == [
        "2025-yil mart – 2025-yil sentabr | Perfect Consulting kompaniyasi | Proyekt manager",
        "2026-yil yanvar – 2026-yil may | Innovatsion rivojlanish agentligi | dasturchi",
        "2026-yil aprel – hozir | Big IT kompaniyasi | dasturchi",
    ]
    assert "pending_employment_entries" not in draft.data
