from app.services.resume_flow import (
    OBJECTIVE_STEPS,
    STEPS,
    build_preview,
    next_step,
    parse_answer,
    previous_step,
    split_preview,
    validate_answer,
)


def test_steps_have_a_complete_sequence() -> None:
    assert STEPS[0].key == "full_name"
    assert next_step("full_name").key == "job_title"
    assert next_step("languages") is None
    assert previous_step("job_title").key == "full_name"
    assert previous_step("full_name") is None
    assert next_step("objective_full_name", "objective").key == "objective_position"
    assert next_step(OBJECTIVE_STEPS[-1].key, "objective") is None


def test_list_answers_are_collected_one_item_at_a_time() -> None:
    skills_step = next(step for step in STEPS if step.key == "skills")
    experience_step = next(step for step in STEPS if step.key == "experience")
    assert parse_answer(skills_step, "Python") == ["Python"]
    assert parse_answer(experience_step, "Example LLC, 2022–2025") == ["Example LLC, 2022–2025"]
    assert parse_answer(experience_step, "-") == []


def test_contact_validation() -> None:
    email_step = next(step for step in STEPS if step.key == "email")
    phone_step = next(step for step in STEPS if step.key == "phone")
    assert validate_answer(email_step, "invalid") is not None
    assert validate_answer(email_step, "ali@example.com") is None
    assert validate_answer(phone_step, "123") is not None
    assert validate_answer(phone_step, "+998 90 123 45 67") is None


def test_preview_escapes_telegram_html() -> None:
    preview = build_preview(
        {
            "full_name": "Ali <script>",
            "job_title": "Backend & API",
            "skills": ["Python <3"],
        }
    )
    assert "<script>" not in preview
    assert "Ali &lt;script&gt;" in preview
    assert "Backend &amp; API" in preview


def test_preview_splits_on_section_boundaries() -> None:
    preview = "first section\n\nsecond section\n\nthird section"
    assert split_preview(preview, max_length=30) == [
        "first section\n\nsecond section",
        "third section",
    ]


def test_preview_supports_objective_and_custom_sections() -> None:
    preview = build_preview(
        {
            "document_type": "objective",
            "objective_full_name": "Ali Valiyev",
            "custom_sections": [{"title": "Sertifikatlar", "content": "IELTS 7.5"}],
        }
    )
    assert "MA’LUMOTNOMA" in preview
    assert "Ali Valiyev" in preview
    assert "Sertifikatlar" in preview
