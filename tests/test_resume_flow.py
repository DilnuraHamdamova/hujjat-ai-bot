import pytest

from app.services.resume_flow import (
    OBJECTIVE_STEPS,
    STEP_BY_KEY,
    STEPS,
    EmploymentEntry,
    build_preview,
    next_step,
    normalize_answer,
    parse_answer,
    parse_employment_entries,
    previous_step,
    split_preview,
    validate_answer,
)


def test_steps_have_a_complete_sequence() -> None:
    assert STEPS[0].key == "full_name"
    assert next_step("full_name").key == "job_title"
    assert next_step("job_title").key == "skills"
    assert next_step("skills").key == "phone"
    assert next_step("languages") is None
    assert previous_step("job_title").key == "full_name"
    assert previous_step("full_name") is None
    assert next_step("objective_full_name", "objective").key == "objective_position"
    assert next_step(OBJECTIVE_STEPS[-1].key, "objective") is None


def test_objective_education_is_completed_before_add_more() -> None:
    graduated = STEP_BY_KEY["objective_graduated"]
    assert graduated.is_list is False
    assert next_step("objective_education_level", "objective").key == "objective_graduated"
    assert next_step("objective_graduated", "objective").key == "objective_specialty"
    assert "objective_relative_address" in STEP_BY_KEY
    assert STEP_BY_KEY["objective_employment"].is_list is True


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


def test_relative_birth_requires_full_date_and_place() -> None:
    step = STEP_BY_KEY["objective_relative_birth"]
    assert validate_answer(step, "1965-yil, Toshkent") is not None
    assert validate_answer(step, "31.02.1965, Toshkent") is not None
    assert validate_answer(step, "20.03.1965") is not None
    assert validate_answer(step, "20.03.1965, Toshkent shahri") is None


def test_optional_objective_dash_is_rendered_as_no() -> None:
    assert STEP_BY_KEY["objective_party"].optional is True


def test_spoken_party_non_membership_is_normalized() -> None:
    party_step = STEP_BY_KEY["objective_party"]

    assert normalize_answer(party_step, "Partiyaviyligim yo'q") == "-"
    assert normalize_answer(party_step, "Partiyaga a’zo emasman") == "-"
    assert parse_answer(party_step, "Partiyaviyligim yo'q") == ""
    assert parse_answer(party_step, "Partiyaga a’zo emasman") == ""


def test_spoken_employment_is_converted_to_document_format() -> None:
    employment_step = STEP_BY_KEY["objective_employment"]

    assert parse_answer(
        employment_step,
        (
            "Big IT kompaniyasida 2025 yil martdan 2025 yil sentabrgacha "
            "Proyekt manager bo'lib ishlaganman"
        ),
    ) == [
        "2025-yil mart – 2025-yil sentabr | Big IT kompaniyasi | Proyekt manager"
    ]


@pytest.mark.parametrize(
    ("step_key", "spoken", "expected"),
    [
        ("full_name", "Mening ismim va familiyam Ali Valiyev", "Ali Valiyev"),
        ("job_title", "Men Backend dasturchi bo'lib ishlayman", "Backend dasturchi"),
        ("phone", "Telefonim +998 90 123 45 67", "+998 90 123 45 67"),
        ("email", "Emailim ali@example.com bo‘ladi", "ali@example.com"),
        ("location", "Men Toshkent shahrida yashayman", "Toshkent shahri"),
        ("objective_position", "Big IT kompaniyasida menejer bo'lib ishlayman", "menejer"),
        ("objective_birth_date", "1998-yil 12-martda tug'ilganman", "12.03.1998"),
        ("objective_birth_place", "Toshkent shahrida tug'ilganman", "Toshkent shahri"),
        ("objective_nationality", "Millatim o'zbek", "o'zbek"),
        ("objective_party", "XDP partiyasiga a'zoman", "XDP"),
        ("objective_education_level", "Ma'lumotim oliy", "oliy"),
        (
            "objective_graduated",
            "TDIUda 2021 yildan 2025 yilgacha o'qiganman",
            "TDIU, 2021–2025",
        ),
        ("objective_specialty", "Mutaxassisligim iqtisodiyot", "iqtisodiyot"),
        ("objective_degree", "Ilmiy darajam PhD", "PhD"),
        ("objective_title", "Ilmiy unvonim dotsent", "dotsent"),
        ("objective_awards", "Do'stlik ordeni bilan taqdirlanganman", "Do'stlik ordeni"),
        ("objective_elected", "A'zoligim Tuman Kengashi deputati", "Tuman Kengashi deputati"),
        (
            "objective_relative_birth",
            "1965-yil 20-martda Toshkent shahrida tug'ilgan",
            "20.03.1965, Toshkent shahri",
        ),
        ("objective_relative_work", "TDIUda professor bo'lib ishlaydi", "TDIU, professor"),
        (
            "objective_relative_address",
            "U Toshkent shahri Chilonzor tumanida yashaydi",
            "Toshkent shahri Chilonzor tumani",
        ),
    ],
)
def test_spoken_answers_are_normalized_for_form_fields(
    step_key: str, spoken: str, expected: str
) -> None:
    assert normalize_answer(STEP_BY_KEY[step_key], spoken) == expected


def test_spoken_skills_are_split_into_separate_values() -> None:
    assert parse_answer(
        STEP_BY_KEY["skills"], "Python, Docker va Gitni bilaman"
    ) == ["Python", "Docker", "Git"]


def test_multiple_employments_are_split_and_missing_details_are_detected() -> None:
    entries = parse_employment_entries(
        "Perfect Consulting kompaniyasida 2025-yil martdan 2025-yil sentabrgacha "
        "ishlaganman, 2026-yil yanvardan maygacha Innovatsion rivojlanish "
        "agentligida dasturchi bolib, 2026-yil apreldan hozirgacha dasturchi "
        "bolib Big IT kompaniyasida ishlaganman"
    )

    assert entries == [
        EmploymentEntry(
            period="2025-yil mart – 2025-yil sentabr",
            workplace="Perfect Consulting kompaniyasi",
            position=None,
        ),
        EmploymentEntry(
            period="2026-yil yanvar – 2026-yil may",
            workplace="Innovatsion rivojlanish agentligi",
            position="dasturchi",
        ),
        EmploymentEntry(
            period="2026-yil aprel – hozir",
            workplace="Big IT kompaniyasi",
            position="dasturchi",
        ),
    ]


def test_employment_parser_preserves_known_fields_when_another_is_missing() -> None:
    entries = parse_employment_entries(
        "A kompaniyasida 2025 yil martdan sentabrgacha dasturchi bo'lib "
        "ishlaganman, B kompaniyasida menejer bo'lib ishlaganman"
    )

    assert entries[0].complete is True
    assert entries[1] == EmploymentEntry(
        period=None,
        workplace="B kompaniyasi",
        position="menejer",
    )


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
