from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from zipfile import ZipFile

from app.bot.keyboards import (
    QUESTION_EXAMPLES,
    cv_template_keyboard,
    document_type_keyboard,
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
    portfolio_token_keyboard,
    question_navigation_keyboard,
    relative_more_keyboard,
    relatives_keyboard,
    skill_suggestions_keyboard,
    start_keyboard,
)
from app.documents.generator import DocumentGenerator
from app.services.localization import normalize_language, step_prompt, text
from app.services.portfolio import render_portfolio
from app.services.resume_flow import OBJECTIVE_STEPS, STEP_BY_KEY, build_preview, validate_answer
from app.services.templates import TEMPLATE_CODES


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
    ]


def test_only_optional_questions_have_skip_button() -> None:
    required_callbacks = [
        button.callback_data
        for button in question_navigation_keyboard("objective_full_name", "uz").inline_keyboard[0]
    ]
    optional_callbacks = [
        button.callback_data
        for button in question_navigation_keyboard("objective_party", "uz").inline_keyboard[0]
    ]
    assert required_callbacks == ["flow:back:objective_full_name"]
    assert optional_callbacks == ["flow:back:objective_party", "flow:skip:objective_party"]


def test_template_gallery_uses_telegram_webapp_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.bot.keyboards.get_settings",
        lambda: SimpleNamespace(template_webapp_url="https://example.com/webapp/templates"),
    )
    keyboard = cv_template_keyboard("uz")
    open_button = keyboard.inline_keyboard[0][0]
    assert open_button.web_app is not None
    assert open_button.web_app.url == "https://example.com/webapp/templates"
    assert "Shablonlarni ko‘rish" in open_button.text
    assert keyboard.inline_keyboard[-1][0].callback_data == "document:choose"


def test_cv_photo_is_optional_without_template_back_button() -> None:
    keyboard = photo_navigation_keyboard("uz", "cv")
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert callbacks == ["photo:skip"]
    assert "Rasmsiz davom etish" in keyboard.inline_keyboard[0][0].text


def test_all_objective_questions_have_examples() -> None:
    objective_questions = {
        step.key for step in OBJECTIVE_STEPS if step.key != "objective_relatives"
    }
    assert objective_questions <= QUESTION_EXAMPLES.keys()
    assert all(
        not any(
            button.callback_data == f"example:{key}"
            for row in question_navigation_keyboard(key, "uz").inline_keyboard
            for button in row
        )
        for key in objective_questions
    )


def test_education_and_relative_keyboards_have_guided_actions() -> None:
    education_levels = objective_education_level_keyboard("uz").inline_keyboard
    assert [row[0].text for row in education_levels[:-1]] == [
        "Oliy",
        "Tugallanmagan oliy",
        "O‘rta maxsus",
        "O‘rta",
    ]
    assert all("Bakalavr" not in row[0].text for row in education_levels)
    assert [row[0].callback_data for row in education_more_keyboard("uz").inline_keyboard] == [
        "education:add",
        "education:done",
        "flow:back",
    ]
    relative_buttons = relatives_keyboard(["mother", "older_sister"], "uz")
    flattened = [button for row in relative_buttons.inline_keyboard for button in row]
    assert any(button.text == "✅ Onasi" for button in flattened)
    assert any(button.text == "✅ Opasi" for button in flattened)
    assert any(button.callback_data == "relative:types:done" for button in flattened)
    assert [row[0].callback_data for row in relative_more_keyboard("uz").inline_keyboard] == [
        "relative:add_same",
        "relative:next",
        "flow:back",
    ]


def test_template_preview_images_exist() -> None:
    preview_dir = Path("app/assets/template_previews")
    for template_code in TEMPLATE_CODES:
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
    assert text("portfolio_ready_prompt", "ru") == (
        "Пример понятен? Начнём создавать ваше портфолио?"
    )
    assert "Namuna" not in text("portfolio_ready_prompt", "ru")
    assert "Section saved" in text(
        "portfolio_section_saved", "en", prompt="Projects"
    )


def test_skill_suggestions_are_renderable_for_job_title() -> None:
    keyboard = skill_suggestions_keyboard("Java Backend dasturchi", "uz")
    buttons = [button for row in keyboard.inline_keyboard for button in row]
    assert any(button.callback_data == "skill:suggest:java" for button in buttons)
    assert text("skill_suggestions_hint", "uz") == "Lavozimingizga mos ko‘nikmalar:"


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


def test_portfolio_flow_has_example_link_order_and_back_buttons() -> None:
    ready = portfolio_ready_keyboard("uz", "https://demo.netlify.app")
    assert ready.inline_keyboard[0][0].url == "https://demo.netlify.app?lang=uz"
    assert (
        portfolio_ready_keyboard("ru", "https://demo.netlify.app?ref=bot").inline_keyboard[0][0].url
        == "https://demo.netlify.app?ref=bot&lang=ru"
    )
    assert ready.inline_keyboard[-1][0].callback_data == "portfolio:back:documents"
    assert portfolio_template_keyboard("uz").inline_keyboard[-1][0].callback_data == (
        "portfolio:back:example"
    )
    sections = portfolio_sections_keyboard(
        "uz", ["achievements", "about", "profile"]
    ).inline_keyboard
    callbacks = [row[0].callback_data for row in sections]
    assert callbacks[:5] == [
        "portfolio-section:profile",
        "portfolio-section:about",
        "portfolio-section:skills",
        "portfolio-section:experience",
        "portfolio-section:education",
    ]
    assert callbacks[-2:] == ["portfolio:start", "portfolio:back:templates"]
    assert portfolio_step_keyboard("uz").inline_keyboard[0][0].callback_data == (
        "portfolio:back:section"
    )
    assert portfolio_review_keyboard("uz").inline_keyboard[0][0].callback_data == (
        "portfolio:back:last"
    )
    assert portfolio_token_keyboard("uz").inline_keyboard[0][0].callback_data == (
        "portfolio:back:review"
    )


def test_generated_portfolio_renders_all_supported_content() -> None:
    document = render_portfolio(
        {
            "portfolio_template": "developer",
            "full_name": "Ali & Vali",
            "job_title": "Backend Developer",
            "portfolio_tagline": "Reliable products",
            "summary": "About me",
            "skills": ["Python", "PostgreSQL"],
            "experience": ["Senior Engineer"],
            "education": ["BSc Software Engineering"],
            "languages": ["English — C1"],
            "email": "ali@example.com",
            "phone": "+998 90 000 00 00",
            "location": "Tashkent",
            "portfolio_sections": [
                {
                    "key": "projects",
                    "title": "Projects",
                    "content": "Hujjat AI https://example.com/demo",
                },
                {"key": "certificates", "title": "Certificates", "content": "AWS"},
                {"key": "publications", "title": "Publications", "content": "Article"},
                {"key": "achievements", "title": "Achievements", "content": "Award"},
                {"key": "links", "title": "Links", "content": "https://github.com/example"},
            ],
        },
        "en",
    )
    for value in (
        "Ali &amp; Vali",
        "About",
        "Skills",
        "Experience",
        "Education",
        "Languages",
        "Projects",
        "Certificates",
        "Publications",
        "Achievements",
        "Links",
        "Contact",
    ):
        assert value in document
    assert 'target="_blank"' in document
    assert 'href="https://example.com/demo"' in document
    assert 'href="https://github.com/example"' in document
    assert "grid-template-columns:1fr" in document


def test_generated_portfolio_uses_selected_language_everywhere() -> None:
    data = {
        "full_name": "Alex Morgan",
        "job_title": "Инженер-программист",
        "summary": "Создаю надёжные продукты.",
        "skills": ["Python"],
        "experience": ["Nexus Labs"],
        "education": ["ТУИТ"],
        "languages": ["Русский — C2"],
        "portfolio_sections": [
            {"key": "projects", "title": "Projects", "content": "Pulse"},
            {"key": "achievements", "title": "Achievements", "content": "Award"},
        ],
    }
    russian = render_portfolio(data, "ru")
    assert '<html lang="ru">' in russian
    for value in ("Обо мне", "Навыки", "Опыт работы", "Образование", "Языки", "Проекты"):
        assert value in russian
    assert "Достижения / Влог" in russian
    assert "Built with care" not in russian

    uzbek = render_portfolio(data, "uz")
    assert '<html lang="uz">' in uzbek
    assert "Men haqimda" in uzbek
    assert "Bog‘lanish" in uzbek
