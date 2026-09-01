from dataclasses import dataclass
from html import escape

from app.services.localization import (
    OBJECTIVE_LABELS,
    PREVIEW_LABELS,
    normalize_language,
    text,
)
from app.services.resume_schema import ResumeData


@dataclass(frozen=True)
class Step:
    key: str
    prompt: str
    is_list: bool = False
    optional: bool = False


CV_STEPS = (
    Step("full_name", "Ism va familiyangizni kiriting:"),
    Step("job_title", "Qaysi lavozim uchun CV tayyorlaymiz?"),
    Step("phone", "Telefon raqamingizni kiriting:"),
    Step("email", "Email manzilingizni kiriting:"),
    Step("location", "Yashash joyingizni kiriting (masalan, Toshkent):"),
    Step("summary", "O‘zingiz haqingizda qisqa professional ma’lumot yozing:"),
    Step("skills", "Ko‘nikmalaringizni vergul bilan ajratib yozing:", is_list=True),
    Step(
        "experience",
        "Ish tajribangizni yozing. Har bir ish joyini yangi qatordan kiriting. "
        "Tajriba bo‘lmasa '-' yuboring:",
        is_list=True,
        optional=True,
    ),
    Step(
        "education",
        "Ta’lim ma’lumotlaringizni yozing. Har birini yangi qatordan kiriting:",
        is_list=True,
    ),
    Step(
        "languages",
        "Tillar va darajalarni kiriting (masalan: O‘zbek — ona tili, Ingliz — B2):",
        is_list=True,
    ),
)

OBJECTIVE_STEPS = (
    Step("objective_full_name", "", optional=False),
    Step("objective_position", ""),
    Step("objective_birth_date", ""),
    Step("objective_birth_place", ""),
    Step("objective_nationality", ""),
    Step("objective_party", "", optional=True),
    Step("objective_education_level", ""),
    Step("objective_graduated", "", is_list=True),
    Step("objective_specialty", ""),
    Step("objective_degree", "", optional=True),
    Step("objective_title", "", optional=True),
    Step("objective_languages", "", is_list=True),
    Step("objective_awards", "", optional=True),
    Step("objective_elected", "", optional=True),
    Step("objective_employment", "", is_list=True),
    Step("objective_relatives", "", is_list=True),
)

# Backwards-compatible names used by existing tests and CV edit controls.
STEPS = CV_STEPS
STEP_BY_KEY = {step.key: step for step in (*CV_STEPS, *OBJECTIVE_STEPS)}


def steps_for(document_type: str) -> tuple[Step, ...]:
    return OBJECTIVE_STEPS if document_type == "objective" else CV_STEPS


def parse_answer(step: Step, text: str) -> str | list[str]:
    clean = text.strip()
    if step.optional and clean == "-":
        return [] if step.is_list else ""
    if step.is_list:
        item = clean.strip(" •-")
        return [item] if item else []
    return clean


def next_step(current_key: str, document_type: str = "cv") -> Step | None:
    steps = steps_for(document_type)
    for index, step in enumerate(steps):
        if step.key == current_key:
            return steps[index + 1] if index + 1 < len(steps) else None
    return steps[0]


def validate_answer(step: Step, answer: str, language: str = "uz") -> str | None:
    clean = answer.strip()
    if not clean:
        return text("empty_answer", language)
    if len(clean) > 600:
        return text("long_answer", language)
    if step.key == "email" and ("@" not in clean or "." not in clean.rsplit("@", 1)[-1]):
        return text("invalid_email", language)
    if step.key == "phone" and sum(character.isdigit() for character in clean) < 7:
        return text("invalid_phone", language)
    return None


def build_preview(data: dict[str, object], language: str = "uz") -> str:
    if data.get("document_type") == "objective":
        return _build_objective_preview(data, language)

    resume = ResumeData.model_validate(data)
    labels = PREVIEW_LABELS[normalize_language(language)]

    def joined(items: list[str]) -> str:
        return "\n".join(f"• {escape(item)}" for item in items) or "—"

    def safe(value: str | None) -> str:
        return escape(value) if value else "—"

    scalar_fields = (
        ("full_name", resume.full_name),
        ("job_title", resume.job_title),
        ("phone", resume.phone),
        ("email", resume.email),
        ("location", resume.location),
    )
    sections = [f"<b>{labels['title']}</b>"]
    contacts = [
        f"<b>{labels[key]}:</b> {safe(value)}" for key, value in scalar_fields if key in data
    ]
    if contacts:
        sections.append("\n".join(contacts))
    if "summary" in data:
        sections.append(f"<b>{labels['summary']}:</b>\n{safe(resume.summary)}")
    for key, values in (
        ("skills", resume.skills),
        ("experience", resume.experience),
        ("education", resume.education),
        ("languages", resume.languages),
    ):
        if key in data:
            sections.append(f"<b>{labels[key]}:</b>\n{joined(values)}")
    sections.extend(_custom_preview_sections(data))
    return "\n\n".join(sections)


def _build_objective_preview(data: dict[str, object], language: str) -> str:
    labels = OBJECTIVE_LABELS[normalize_language(language)]
    fields = (
        ("objective_full_name", "relative_name"),
        ("objective_position", "position"),
        ("objective_birth_date", "birth_date"),
        ("objective_birth_place", "birth_place"),
        ("objective_nationality", "nationality"),
        ("objective_party", "party"),
        ("objective_education_level", "education_level"),
        ("objective_graduated", "graduated"),
        ("objective_specialty", "specialty"),
        ("objective_degree", "degree"),
        ("objective_title", "academic_title"),
        ("objective_languages", "foreign_languages"),
        ("objective_awards", "awards"),
        ("objective_elected", "elected"),
        ("objective_employment", "employment"),
        ("objective_relatives", "relatives"),
    )
    sections = [f"<b>{labels['document_title']}</b>"]
    for key, label_key in fields:
        if key not in data:
            continue
        value = data[key]
        if isinstance(value, list):
            rendered = "\n".join(f"• {escape(str(item))}" for item in value) or "—"
            sections.append(f"<b>{labels[label_key]}:</b>\n{rendered}")
        else:
            sections.append(f"<b>{labels[label_key]}:</b> {escape(str(value)) or '—'}")
    sections.extend(_custom_preview_sections(data))
    return "\n\n".join(sections)


def _custom_preview_sections(data: dict[str, object]) -> list[str]:
    raw_sections = data.get("custom_sections", [])
    if not isinstance(raw_sections, list):
        return []
    sections: list[str] = []
    for item in raw_sections:
        if not isinstance(item, dict):
            continue
        title = escape(str(item.get("title", "")))
        content = escape(str(item.get("content", "")))
        if title and content:
            sections.append(f"<b>{title}:</b>\n{content}")
    return sections


def split_preview(preview: str, max_length: int = 3500) -> list[str]:
    """Split on section boundaries without cutting Telegram HTML markup."""
    chunks: list[str] = []
    current = ""
    for section in preview.split("\n\n"):
        candidate = f"{current}\n\n{section}" if current else section
        if len(candidate) <= max_length:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = section
    if current:
        chunks.append(current)
    return chunks
