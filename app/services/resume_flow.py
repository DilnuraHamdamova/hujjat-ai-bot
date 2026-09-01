from dataclasses import dataclass
from html import escape

from app.services.resume_schema import ResumeData


@dataclass(frozen=True)
class Step:
    key: str
    prompt: str
    is_list: bool = False
    optional: bool = False


STEPS = (
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

STEP_BY_KEY = {step.key: step for step in STEPS}


def parse_answer(step: Step, text: str) -> str | list[str]:
    clean = text.strip()
    if step.optional and clean == "-":
        return [] if step.is_list else ""
    if step.is_list:
        separator = "\n" if "\n" in clean else ","
        return [part.strip(" •-") for part in clean.split(separator) if part.strip(" •-")]
    return clean


def next_step(current_key: str) -> Step | None:
    for index, step in enumerate(STEPS):
        if step.key == current_key:
            return STEPS[index + 1] if index + 1 < len(STEPS) else None
    return STEPS[0]


def validate_answer(step: Step, text: str) -> str | None:
    clean = text.strip()
    if not clean:
        return "Javob bo‘sh bo‘lmasligi kerak."
    if len(clean) > 600:
        return "Javob juda uzun. 600 belgidan qisqaroq yozing."
    if step.key == "email" and ("@" not in clean or "." not in clean.rsplit("@", 1)[-1]):
        return "Email manzil noto‘g‘ri ko‘rinmoqda. Masalan: ali@example.com"
    if step.key == "phone" and sum(character.isdigit() for character in clean) < 7:
        return "Telefon raqamini to‘liq kiriting. Masalan: +998 90 123 45 67"
    return None


def build_preview(data: dict[str, object]) -> str:
    resume = ResumeData.model_validate(data)

    def joined(items: list[str]) -> str:
        return "\n".join(f"• {escape(item)}" for item in items) or "—"

    def safe(value: str | None) -> str:
        return escape(value) if value else "—"

    return (
        "<b>CV ma’lumotlarini tekshiring</b>\n\n"
        f"<b>Ism:</b> {safe(resume.full_name)}\n"
        f"<b>Lavozim:</b> {safe(resume.job_title)}\n"
        f"<b>Telefon:</b> {safe(resume.phone)}\n"
        f"<b>Email:</b> {safe(resume.email)}\n"
        f"<b>Manzil:</b> {safe(resume.location)}\n\n"
        f"<b>Profil:</b>\n{safe(resume.summary)}\n\n"
        f"<b>Ko‘nikmalar:</b>\n{joined(resume.skills)}\n\n"
        f"<b>Tajriba:</b>\n{joined(resume.experience)}\n\n"
        f"<b>Ta’lim:</b>\n{joined(resume.education)}\n\n"
        f"<b>Tillar:</b>\n{joined(resume.languages)}"
    )


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
