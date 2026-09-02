from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from app.bot.keyboards import (
    document_type_keyboard,
    language_keyboard,
    output_format_keyboard,
    question_navigation_keyboard,
    start_keyboard,
)
from app.documents.generator import DocumentGenerator
from app.services.localization import normalize_language, step_prompt
from app.services.resume_flow import STEP_BY_KEY, build_preview, validate_answer


def test_language_keyboard_has_three_supported_languages() -> None:
    callbacks = [button.callback_data for button in language_keyboard().inline_keyboard[0]]
    assert callbacks == ["language:uz", "language:en", "language:ru"]


def test_document_and_output_choices_are_available() -> None:
    document_callbacks = [
        row[0].callback_data for row in document_type_keyboard("uz").inline_keyboard
    ]
    assert document_callbacks == [
        "document:cv",
        "document:objective",
        "document:recommendation",
        "document:portfolio",
    ]
    assert [row[0].callback_data for row in output_format_keyboard().inline_keyboard] == [
        "format:pdf",
        "format:docx",
    ]
    navigation = question_navigation_keyboard("education", "en").inline_keyboard[0]
    assert [button.callback_data for button in navigation] == [
        "flow:back:education",
        "flow:skip:education",
    ]


def test_template_preview_images_exist() -> None:
    preview_dir = Path("app/assets/template_previews")
    for template_code in ("classic", "modern", "europass"):
        preview = preview_dir / f"{template_code}.png"
        assert preview.is_file()
        assert preview.stat().st_size > 10_000
    assert (preview_dir / "sample-profile.png").stat().st_size > 10_000


def test_bot_copy_uses_selected_language() -> None:
    assert normalize_language("en-US") == "en"
    assert normalize_language("de") == "uz"
    assert step_prompt("full_name", "ru") == "Введите имя и фамилию:"
    assert start_keyboard("en").inline_keyboard[0][0].text == "📝 Create a new document"
    assert validate_answer(STEP_BY_KEY["email"], "invalid", "ru") == (
        "Некорректный email. Пример: ali@example.com"
    )
    assert "Review your resume information" in build_preview({"full_name": "Ali"}, "en")


def test_docx_headings_use_selected_language(tmp_path) -> None:
    artifacts = DocumentGenerator(tmp_path).generate(
        uuid4(),
        {"full_name": "Ali", "summary": "Developer", "skills": ["Python"]},
        "en",
    )
    docx_path = next(artifact.path for artifact in artifacts if artifact.format == "docx")
    with ZipFile(docx_path) as archive:
        document_xml = archive.read("word/document.xml").decode()
    assert "PROFILE" in document_xml
    assert "SKILLS" in document_xml
