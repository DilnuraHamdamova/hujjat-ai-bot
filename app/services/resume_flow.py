import re
from dataclasses import dataclass
from datetime import datetime
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


@dataclass(frozen=True)
class EmploymentEntry:
    period: str | None = None
    workplace: str | None = None
    position: str | None = None

    @property
    def complete(self) -> bool:
        return bool(self.period and self.workplace and self.position)

    def render(self) -> str:
        return " | ".join(
            value for value in (self.period, self.workplace, self.position) if value
        )


CV_STEPS = (
    Step("full_name", "Ism va familiyangizni kiriting:"),
    Step("job_title", "Qaysi lavozim uchun CV tayyorlaymiz?"),
    Step("skills", "Ko‘nikmalaringizni vergul bilan ajratib yozing:", is_list=True),
    Step("phone", "Telefon raqamingizni kiriting:"),
    Step("email", "Email manzilingizni kiriting:"),
    Step("location", "Yashash joyingizni kiriting (masalan, Toshkent):"),
    Step("summary", "O‘zingiz haqingizda qisqa professional ma’lumot yozing:"),
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
    Step("objective_graduated", ""),
    Step("objective_specialty", ""),
    Step("objective_degree", "", optional=True),
    Step("objective_title", "", optional=True),
    Step("objective_languages", "", is_list=True),
    Step("objective_awards", "", optional=True),
    Step("objective_elected", "", optional=True),
    Step("objective_employment", "", is_list=True, optional=True),
    Step("objective_relatives", "", is_list=True),
)

OBJECTIVE_RELATIVE_STEPS = (
    Step("objective_relative_name", ""),
    Step("objective_relative_birth", ""),
    Step("objective_relative_work", ""),
    Step("objective_relative_address", ""),
)

# Backwards-compatible names used by existing tests and CV edit controls.
STEPS = CV_STEPS
STEP_BY_KEY = {step.key: step for step in (*CV_STEPS, *OBJECTIVE_STEPS, *OBJECTIVE_RELATIVE_STEPS)}


def steps_for(document_type: str) -> tuple[Step, ...]:
    return OBJECTIVE_STEPS if document_type == "objective" else CV_STEPS


def parse_answer(step: Step, text: str) -> str | list[str]:
    clean = normalize_answer(step, text)
    if step.optional and clean == "-":
        return [] if step.is_list else ""
    if step.is_list:
        if step.key == "skills":
            return [item.strip(" •-") for item in clean.split(",") if item.strip(" •-")]
        item = clean.strip(" •-")
        return [item] if item else []
    return clean


_NO_ANSWER_PHRASES = (
    "yo'q",
    "yoq",
    "mavjud emas",
    "a'zo emas",
    "azo emas",
    "partiyaga a'zo emas",
    "partiyaviyligim yo'q",
    "none",
    "not a member",
    "нет",
    "не состою",
)

_UZ_MONTHS = (
    "yanvar",
    "fevral",
    "mart",
    "aprel",
    "may",
    "iyun",
    "iyul",
    "avgust",
    "sentabr",
    "sentyabr",
    "oktabr",
    "oktyabr",
    "noyabr",
    "dekabr",
)
_MONTH_PATTERN = "|".join(_UZ_MONTHS)
_EMPLOYMENT_RANGE = re.compile(
    rf"(?P<start>\d{{4}}\s*(?:-?\s*yil)?\s*(?:{_MONTH_PATTERN})?)\s*dan\s*"
    rf"(?P<end>\d{{4}}\s*(?:-?\s*yil)?\s*(?:{_MONTH_PATTERN})?)\s*gacha",
    re.IGNORECASE,
)
_SPOKEN_EMPLOYMENT_RANGE = re.compile(
    rf"(?P<start_year>\d{{4}})\s*-?\s*(?:yil)?\s*(?P<start_month>{_MONTH_PATTERN})?"
    rf"\s*dan\s*(?:"
    rf"(?P<present>hozir)"
    rf"|(?P<end_year>\d{{4}})\s*-?\s*(?:yil)?\s*(?P<end_month>{_MONTH_PATTERN})?"
    rf"|(?P<end_month_only>{_MONTH_PATTERN})"
    rf")\s*gacha",
    re.IGNORECASE,
)

_WORKPLACE_KINDS = {
    "kompaniyasida": "kompaniyasi",
    "kompaniyada": "kompaniyasi",
    "agentligida": "agentligi",
    "tashkilotida": "tashkiloti",
    "korxonasida": "korxonasi",
    "mchjda": "MCHJ",
}
_WORKPLACE_KIND_PATTERN = "|".join(_WORKPLACE_KINDS)

_MONTH_NUMBERS = {
    "yanvar": 1,
    "fevral": 2,
    "mart": 3,
    "aprel": 4,
    "may": 5,
    "iyun": 6,
    "iyul": 7,
    "avgust": 8,
    "sentabr": 9,
    "sentyabr": 9,
    "oktabr": 10,
    "oktyabr": 10,
    "noyabr": 11,
    "dekabr": 12,
}

_ADJACENT_EMPLOYMENT_RANGE = re.compile(
    rf"(?P<start>\d{{4}}\s*-?\s*yil\s+(?:{_MONTH_PATTERN}))\s+"
    rf"(?P<end>\d{{4}}\s*-?\s*yil\s+(?:{_MONTH_PATTERN}))",
    re.IGNORECASE,
)
_GENERIC_WORKPLACES = {
    "maktabda", "maktabida", "universitetda", "universitetida",
    "kollejda", "kollejida", "litseyda", "litseyida", "tashkilotda",
    "tashkilotida", "muassasada", "muassasasida", "korxonada", "korxonasida",
}


def normalize_employment_period(value: str) -> str | None:
    clean = _apostrophes(value)
    match = _SPOKEN_EMPLOYMENT_RANGE.search(clean)
    if match is None:
        adjacent = _ADJACENT_EMPLOYMENT_RANGE.search(clean)
        if adjacent:
            start = re.sub(r"\s+", " ", adjacent.group("start")).strip()
            end = re.sub(r"\s+", " ", adjacent.group("end")).strip()
            return f"{start}dan {end}gacha"
        canonical = re.search(
            r"(?P<start>\d{4}(?:-yil)?(?:\s+[A-Za-zА-Яа-я]+)?)\s*[–—-]\s*"
            r"(?P<end>(?:\d{4}(?:-yil)?(?:\s+[A-Za-zА-Яа-я]+)?|hozir))",
            clean,
            flags=re.IGNORECASE,
        )
        return (
            f"{canonical.group('start')} – {canonical.group('end')}" if canonical else None
        )
    start = match.group("start_year")
    if match.group("start_month"):
        start = f"{start}-yil {match.group('start_month').casefold()}"
    if match.group("present"):
        end = "hozir"
    else:
        end_year = match.group("end_year") or match.group("start_year")
        end_month = match.group("end_month") or match.group("end_month_only")
        end = f"{end_year}-yil"
        if end_month:
            end = f"{end} {end_month.casefold()}"
    return f"{start} – {end}"


def parse_employment_entries(value: str) -> list[EmploymentEntry]:
    """Parse one spoken message into one or more employment records."""
    clean = _apostrophes(" ".join(value.strip().split()))
    if not clean:
        return []
    canonical_parts = [part.strip() for part in clean.split("|")]
    if len(canonical_parts) >= 3:
        return [
            EmploymentEntry(
                period=canonical_parts[0] or None,
                workplace=canonical_parts[1] or None,
                position=" | ".join(canonical_parts[2:]) or None,
            )
        ]

    clauses = re.split(
        rf",\s*(?=(?:\d{{4}}\s*-?\s*(?:yil)?|[^,]+?\s+"
        rf"(?:{_WORKPLACE_KIND_PATTERN})))",
        clean,
        flags=re.IGNORECASE,
    )
    entries: list[EmploymentEntry] = []
    for clause in clauses:
        clause = clause.strip(" ,.;")
        if not clause:
            continue
        range_match = _SPOKEN_EMPLOYMENT_RANGE.search(clause)
        period = normalize_employment_period(clause)
        remainder = clause
        if range_match:
            remainder = f"{clause[:range_match.start()]} {clause[range_match.end():]}"
        else:
            adjacent_range = _ADJACENT_EMPLOYMENT_RANGE.search(clause)
            if adjacent_range:
                remainder = f"{clause[:adjacent_range.start()]} {clause[adjacent_range.end():]}"
        remainder = re.sub(r"^(?:va\s+|keyin\s+)", "", remainder, flags=re.IGNORECASE)
        remainder = re.sub(
            r"\s+(?:ishlaganman|ishladim|ishlayman)\.?$",
            "",
            remainder,
            flags=re.IGNORECASE,
        ).strip(" ,.-")

        workplace: str | None = None
        position: str | None = None
        position_first = re.match(
            rf"(?P<position>.+?)\s+bo'?lib\s+(?P<name>.+?)\s+"
            rf"(?P<kind>{_WORKPLACE_KIND_PATTERN})$",
            remainder,
            flags=re.IGNORECASE,
        )
        if position_first:
            position = position_first.group("position").strip(" ,.-")
            workplace = _canonical_workplace(
                position_first.group("name"), position_first.group("kind")
            )
        else:
            workplace_first = re.match(
                rf"(?P<name>.+?)\s+(?P<kind>{_WORKPLACE_KIND_PATTERN})"
                rf"(?:\s+(?P<position>.+?))?$",
                remainder,
                flags=re.IGNORECASE,
            )
            if workplace_first:
                workplace = _canonical_workplace(
                    workplace_first.group("name"), workplace_first.group("kind")
                )
                raw_position = (workplace_first.group("position") or "").strip(" ,.-")
                raw_position = re.sub(
                    r"\s+bo'?lib$", "", raw_position, flags=re.IGNORECASE
                ).strip()
                if raw_position and raw_position.casefold() not in {
                    "ishlaganman",
                    "ishladim",
                    "ishlayman",
                }:
                    position = raw_position

        if workplace is None and position is None:
            titled_workplace = re.match(
                r"(?P<workplace>.+?)\s+(?P<position>.+?)\s+lavozimida$",
                remainder,
                flags=re.IGNORECASE,
            )
            if titled_workplace:
                workplace = normalize_employment_workplace(
                    titled_workplace.group("workplace")
                )
                position = titled_workplace.group("position").strip(" ,.-")

        if workplace is None and position is None:
            generic_workplace = re.match(
                r"(?P<workplace>.+?(?:da|de)(?=\s))\s+(?P<position>.+)$",
                remainder,
                flags=re.IGNORECASE,
            )
            if generic_workplace:
                workplace = normalize_employment_workplace(
                    generic_workplace.group("workplace")
                )
                if workplace and not is_specific_employment_workplace(workplace):
                    workplace = None
                position = re.sub(
                    r"\s+bo'?lib$",
                    "",
                    generic_workplace.group("position"),
                    flags=re.IGNORECASE,
                ).strip(" ,.-")

        if workplace is None and position is None:
            standalone_position = re.sub(
                r"\s+bo'?lib$", "", remainder, flags=re.IGNORECASE
            ).strip(" ,.-")
            if standalone_position:
                position = standalone_position

        if period or workplace or position:
            entries.append(
                EmploymentEntry(period=period, workplace=workplace, position=position)
            )
    return entries


def _canonical_workplace(name: str, kind: str) -> str:
    clean_name = re.sub(r"^(?:men\s+)", "", name, flags=re.IGNORECASE).strip(" ,.-")
    canonical_kind = _WORKPLACE_KINDS[kind.casefold()]
    return f"{clean_name} {canonical_kind}"


def normalize_employment_workplace(value: str) -> str | None:
    """Extract a useful workplace from a direct follow-up answer."""
    clean = _apostrophes(" ".join(value.strip().split())).strip(" ,.-")
    clean = re.sub(
        r"^\d{4}\s*[–—-]\s*(?:\d{4}|hozir)\s*"
        r"(?:(?:yillar|yil)\s*)?(?:davrida\s*)?",
        "",
        clean,
        flags=re.IGNORECASE,
    )
    clean = re.sub(r"^(?:men\s+|shu\s+davrda\s+)", "", clean, flags=re.IGNORECASE)
    clean = re.sub(
        r"\s+(?:ishlaganman|ishladim|ishlayman)\.?$",
        "",
        clean,
        flags=re.IGNORECASE,
    ).strip(" ,.-")
    clean = re.sub(r"universituti\b", "universiteti", clean, flags=re.IGNORECASE)
    return clean or None


def is_specific_employment_workplace(value: str) -> bool:
    normalized = _apostrophes(value).strip(" ,.-").casefold()
    return normalized not in _GENERIC_WORKPLACES


def normalize_answer(step: Step, text: str) -> str:
    """Convert conversational form answers into document-ready values."""
    clean = " ".join(text.strip().split())
    comparable = clean.casefold().replace("’", "'").replace("‘", "'")

    if step.optional and any(phrase in comparable for phrase in _NO_ANSWER_PHRASES):
        return "-"

    if step.key in {"objective_employment", "experience"}:
        employment = _normalize_uzbek_employment(clean)
        if employment is not None:
            return employment

    if step.key in {"full_name", "objective_full_name", "objective_relative_name"}:
        return _normalize_full_name(clean)
    if step.key in {"job_title", "objective_position"}:
        return _normalize_position(clean)
    if step.key == "phone":
        return _extract_phone(clean)
    if step.key == "email":
        return _extract_email(clean)
    if step.key == "location":
        return _normalize_location(clean)
    if step.key == "skills":
        return _normalize_skills(clean)
    if step.key in {"languages", "objective_languages"}:
        return _normalize_language_entry(clean)
    if step.key == "objective_birth_date":
        return _normalize_date_answer(clean)
    if step.key == "objective_birth_place":
        return _normalize_birth_place(clean)
    if step.key == "objective_nationality":
        return _normalize_nationality(clean)
    if step.key == "objective_party":
        return _normalize_party(clean)
    if step.key == "objective_education_level":
        return _normalize_education_level(clean)
    if step.key in {"education", "objective_graduated"}:
        education = _normalize_education(clean, objective=step.key == "objective_graduated")
        if education is not None:
            return education
    if step.key == "objective_specialty":
        return _strip_labeled_answer(
            clean,
            (r"mutaxassisligim", r"yo'nalishim", r"soham"),
            (r"bo'ladi", r"hisoblanadi"),
        )
    if step.key == "objective_degree":
        return _strip_labeled_answer(
            clean,
            (r"ilmiy darajam", r"darajam"),
            (r"bo'ladi", r"bor"),
        )
    if step.key == "objective_title":
        return _strip_labeled_answer(
            clean,
            (r"ilmiy unvonim", r"unvonim"),
            (r"bo'ladi", r"bor"),
        )
    if step.key == "objective_awards":
        return _strip_labeled_answer(
            clean,
            (r"davlat mukofotim", r"mukofotim"),
            (r"bilan taqdirlanganman", r"olganman", r"bor"),
        )
    if step.key == "objective_elected":
        return _strip_labeled_answer(
            clean,
            (r"saylanadigan organlardagi a'zoligim", r"a'zoligim"),
            (r"hisoblanadi", r"bo'ladi", r"a'zosiman"),
        )
    if step.key == "objective_relative_birth":
        return _normalize_relative_birth(clean)
    if step.key == "objective_relative_work":
        return _normalize_relative_work(clean)
    if step.key == "objective_relative_address":
        return _normalize_address(clean)
    return clean


def _apostrophes(value: str) -> str:
    return value.replace("’", "'").replace("‘", "'").replace("`", "'")


def _strip_labeled_answer(
    value: str,
    leading_labels: tuple[str, ...],
    trailing_phrases: tuple[str, ...],
) -> str:
    clean = _apostrophes(value).strip(" ,.-")
    labels = "|".join(leading_labels)
    trailing = "|".join(trailing_phrases)
    clean = re.sub(
        rf"^(?:mening\s+)?(?:{labels})\s*(?::|-|—)?\s*",
        "",
        clean,
        flags=re.IGNORECASE,
    )
    clean = re.sub(
        rf"\s+(?:{trailing})\.?$",
        "",
        clean,
        flags=re.IGNORECASE,
    )
    return clean.strip(" ,.-") or value.strip()


def _normalize_full_name(value: str) -> str:
    value = re.sub(
        r"^(?:otamning|onamning|akamning|ukamning|opamning|singlimning|"
        r"turmush o'rtog'imning|farzandimning)\s+",
        "",
        _apostrophes(value),
        flags=re.IGNORECASE,
    )
    clean = _strip_labeled_answer(
        value,
        (
            r"to'liq ism(?:im|i)?",
            r"ism(?:im|i)?\s+(?:va\s+)?familiya(?:m|si)?",
            r"familiya(?:m|si)?\s+(?:va\s+)?ism(?:im|i)?",
            r"ism(?:im|i)?",
            r"f\.?\s*i\.?\s*sh\.?",
        ),
        (r"bo'ladi", r"deb yoziladi"),
    )
    return _capitalize_name(re.sub(r"^men\s+", "", clean, flags=re.IGNORECASE).strip())


def _capitalize_name(value: str) -> str:
    return " ".join(
        word[:1].upper() + word[1:] for word in value.split() if word
    )


def _normalize_position(value: str) -> str:
    clean = _apostrophes(value).strip(" ,.-")
    workplace_match = re.search(
        r"(?:kompaniyasi|korxonasi|tashkiloti)?da\s+(?P<position>.+?)\s+"
        r"(?:lavozimida\s+)?bo'?lib\s+ishla(?:yman|ganman|dim)",
        clean,
        flags=re.IGNORECASE,
    )
    if workplace_match:
        return workplace_match.group("position").strip(" ,.-")
    clean = _strip_labeled_answer(
        clean,
        (r"hozirgi lavozimim", r"lavozimim", r"kasbim"),
        (
            r"lavozimida bo'?lib ishlayman",
            r"bo'?lib ishlayman",
            r"bo'?lib ishlaganman",
            r"bo'ladi",
        ),
    )
    return re.sub(r"^men\s+", "", clean, flags=re.IGNORECASE).strip()


def _extract_phone(value: str) -> str:
    match = re.search(r"(?:\+?\d[\d\s()\-]{5,}\d)", value)
    return " ".join(match.group(0).split()) if match else value.strip()


def _extract_email(value: str) -> str:
    match = re.search(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", value, re.IGNORECASE)
    return match.group(0) if match else value.strip()


def _normalize_location(value: str) -> str:
    clean = _apostrophes(value).strip(" ,.-")
    match = re.match(
        r"^(?:men\s+)?(?P<place>.+?)(?:da|de)\s+"
        r"(?:yashayman|istiqomat qilaman|turaman)\.?$",
        clean,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group("place").strip(" ,.-")
    return _strip_labeled_answer(
        clean,
        (r"yashash joyim", r"manzilim"),
        (r"bo'ladi",),
    )


def _normalize_skills(value: str) -> str:
    clean = _strip_labeled_answer(
        value,
        (r"ko'nikmalarim", r"biladigan texnologiyalarim"),
        (r"ko'nikmalariga egaman", r"texnologiyalarini bilaman", r"ni bilaman"),
    )
    clean = re.sub(r"ni\s+bilaman\.?$", "", clean, flags=re.IGNORECASE).strip()
    return re.sub(r"\s+(?:hamda|va)\s+", ", ", clean, flags=re.IGNORECASE)


def _normalize_language_entry(value: str) -> str:
    clean = _apostrophes(value).strip(" ,.-")
    match = re.search(
        r"(?P<language>[A-Za-zА-Яа-яЁёO'o'g'\-]+)\s+tili(?:ni)?\s+"
        r"(?P<level>A1|A2|B1|B2|C1|C2|ona tili|boshlang'ich|o'rta|yuqori)"
        r"(?:\s+daraja(?:da|sida))?(?:\s+bilaman)?",
        clean,
        flags=re.IGNORECASE,
    )
    if not match:
        return clean
    language = match.group("language")
    return f"{language[:1].upper()}{language[1:]} tili — {match.group('level').upper()}"


def _extract_date(value: str) -> str | None:
    clean = _apostrophes(value).casefold()
    numeric = re.search(r"(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](\d{4})(?!\d)", clean)
    if numeric:
        day, month, year = map(int, numeric.groups())
    else:
        day_first = re.search(
            rf"(?<!\d)(\d{{1,2}})\s*-?\s*({_MONTH_PATTERN})(?:da)?\s+"
            r"(\d{4})(?:\s*-?\s*yil)?",
            clean,
        )
        year_first = re.search(
            rf"(?<!\d)(\d{{4}})(?:\s*-?\s*yil)?\s+(\d{{1,2}})\s*-?\s*"
            rf"({_MONTH_PATTERN})(?:da)?",
            clean,
        )
        if day_first:
            day = int(day_first.group(1))
            month = _MONTH_NUMBERS[day_first.group(2)]
            year = int(day_first.group(3))
        elif year_first:
            year = int(year_first.group(1))
            day = int(year_first.group(2))
            month = _MONTH_NUMBERS[year_first.group(3)]
        else:
            return None
    try:
        parsed = datetime(year, month, day)
    except ValueError:
        return None
    return parsed.strftime("%d.%m.%Y")


def _normalize_date_answer(value: str) -> str:
    return _extract_date(value) or value.strip()


def _normalize_birth_place(value: str) -> str:
    clean = _apostrophes(value).strip(" ,.-")
    match = re.match(
        r"^(?:men\s+)?(?P<place>.+?)(?:da|de)\s+tug'ilganman\.?$",
        clean,
        flags=re.IGNORECASE,
    )
    if match:
        return _capitalize_place(match.group("place"))
    return _capitalize_place(_strip_labeled_answer(
        clean,
        (r"tug'ilgan joyim", r"tug'ilgan manzilim"),
        (r"bo'ladi",),
    ))


def _capitalize_place(value: str) -> str:
    clean = " ".join(value.strip().split())
    region_district = re.match(
        r"^(?P<region>.+?\bviloyati)\s+(?P<district>.+?\btumani)$",
        clean,
        flags=re.IGNORECASE,
    )
    if region_district and "," not in clean:
        clean = f"{region_district.group('region')}, {region_district.group('district')}"
    parts = [part.strip(" ,.-") for part in clean.split(",")]
    return ", ".join(
        part[:1].upper() + part[1:] for part in parts if part
    )


def _normalize_nationality(value: str) -> str:
    clean = _strip_labeled_answer(
        value,
        (r"millatim", r"milliy mansubligim"),
        (r"millatiga mansubman", r"hisoblanadi", r"bo'ladi"),
    )
    match = re.fullmatch(r"(.+?)(?:man)", clean, flags=re.IGNORECASE)
    clean = match.group(1).strip() if match else clean
    if clean.casefold().replace("‘", "'").replace("’", "'") in {"ozbek", "o'zbek"}:
        return "O'zbek"
    return clean[:1].upper() + clean[1:] if clean else clean


def _normalize_party(value: str) -> str:
    clean = _apostrophes(value).strip(" ,.-")
    match = re.match(
        r"(?P<party>.+?)\s+partiyasiga\s+(?:a'zoman|a'zosiman|a'zo bo'lganman)$",
        clean,
        flags=re.IGNORECASE,
    )
    return match.group("party").strip() if match else clean


def _normalize_education_level(value: str) -> str:
    comparable = _apostrophes(value).casefold()
    if "tugallanmagan oliy" in comparable:
        return "tugallanmagan oliy"
    if "o'rta maxsus" in comparable:
        return "o‘rta maxsus"
    if "oliy" in comparable:
        return "oliy"
    if "o'rta" in comparable:
        return "o‘rta"
    return value.strip()


def _normalize_education(value: str, *, objective: bool) -> str | None:
    clean = _apostrophes(value).strip(" ,.-")
    match = _EMPLOYMENT_RANGE.search(clean)
    if match is None:
        return None
    before = clean[: match.start()].strip(" ,.-")
    after = clean[match.end() :].strip(" ,.-")
    if before:
        institution = before
    else:
        institution_match = re.match(
            r"(?P<institution>.+?)(?:da|de)\s+"
            r"(?:o'qiganman|tamomlaganman|ta'lim olganman).*$",
            after,
            flags=re.IGNORECASE,
        )
        institution = (
            institution_match.group("institution") if institution_match else after
        ).strip(" ,.-")
    institution = re.sub(r"^(?:men\s+)", "", institution, flags=re.IGNORECASE)
    institution = re.sub(r"(?:da|de)$", "", institution, flags=re.IGNORECASE).strip()
    institution = _expand_education_institution(institution)
    if not institution:
        return None
    start = re.search(r"\d{4}", match.group("start"))
    end = re.search(r"\d{4}", match.group("end"))
    if start is None or end is None:
        return None
    period = f"{start.group(0)}–{end.group(0)}"
    return f"{institution}, {period}" if objective else f"{period} — {institution}"


_EDUCATION_INSTITUTION_ALIASES = {
    "tdiu": "Toshkent davlat iqtisodiyot universiteti",
    "tatu": "Muhammad al-Xorazmiy nomidagi Toshkent axborot texnologiyalari universiteti",
    "tdu": "Toshkent davlat universiteti",
    "ozmu": "Mirzo Ulug‘bek nomidagi O‘zbekiston Milliy universiteti",
    "o'zmu": "Mirzo Ulug‘bek nomidagi O‘zbekiston Milliy universiteti",
    "tdyu": "Toshkent davlat yuridik universiteti",
}


def _expand_education_institution(value: str) -> str:
    key = re.sub(r"[.\s]+", "", value.casefold())
    return _EDUCATION_INSTITUTION_ALIASES.get(key, _capitalize_place(value))


def _normalize_relative_birth(value: str) -> str:
    date = _extract_date(value)
    if date is None:
        return value.strip()
    clean = _apostrophes(value).strip()
    if "," in clean:
        place = clean.rsplit(",", 1)[-1].strip(" ,.-")
    else:
        place_match = re.search(
            rf"(?:\d{{4}}\s*-?\s*yil\s+\d{{1,2}}\s*-?\s*(?:{_MONTH_PATTERN})"
            rf"|\d{{1,2}}\s*-?\s*(?:{_MONTH_PATTERN})\s+\d{{4}}\s*-?\s*yil)"
            r"(?:da)?\s+(?P<place>.+?)"
            r"(?:da|de)\s+tug'ilgan",
            clean,
            flags=re.IGNORECASE,
        )
        place = place_match.group("place").strip(" ,.-") if place_match else ""
    return f"{date}, {place}" if place else date


def _normalize_relative_work(value: str) -> str:
    clean = _apostrophes(value).strip(" ,.-")
    match = re.match(
        r"^(?:u\s+)?(?P<workplace>.+?)(?:da|de)\s+(?P<position>.+?)\s+"
        r"(?:bo'?lib\s+)?(?:ishlaydi|ishlagan|ishlayapti)\.?$",
        clean,
        flags=re.IGNORECASE,
    )
    if match:
        return f"{match.group('workplace').strip()}, {match.group('position').strip()}"
    return _strip_labeled_answer(
        clean,
        (r"ish joyi va lavozimi", r"ish joyi"),
        (r"bo'ladi",),
    )


def _normalize_address(value: str) -> str:
    clean = _apostrophes(value).strip(" ,.-")
    match = re.match(
        r"^(?:u\s+)?(?P<address>.+?)(?:da|de)\s+"
        r"(?:yashaydi|istiqomat qiladi|turadi)\.?$",
        clean,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group("address").strip(" ,.-")
    return _strip_labeled_answer(
        clean,
        (r"yashash manzili", r"manzili"),
        (r"bo'ladi",),
    )


def _normalize_uzbek_employment(text: str) -> str | None:
    comparable = text.replace("’", "'").replace("‘", "'")
    match = _EMPLOYMENT_RANGE.search(comparable)
    if match is None:
        return None

    workplace = comparable[: match.start()].strip(" ,.-")
    workplace = re.sub(r"^(?:men\s+)", "", workplace, flags=re.IGNORECASE)
    workplace = re.sub(
        r"\s+(?:kompaniyasi(?:da)?|kompaniyada|korxonasi(?:da)?|tashkiloti(?:da)?)$",
        "",
        workplace,
        flags=re.IGNORECASE,
    ).strip()
    if not workplace:
        return None

    suffix_source = comparable[: match.start()].casefold()
    if "kompaniya" in suffix_source:
        workplace = f"{workplace} kompaniyasi"
    elif "korxona" in suffix_source:
        workplace = f"{workplace} korxonasi"
    elif "tashkilot" in suffix_source:
        workplace = f"{workplace} tashkiloti"

    position = comparable[match.end() :].strip(" ,.-")
    position = re.sub(
        r"\s+(?:bo'?lib\s+)?(?:ishlaganman|ishladim|ishlagan|ishlayman)\.?$",
        "",
        position,
        flags=re.IGNORECASE,
    )
    position = re.sub(r"\s+lavozimida$", "", position, flags=re.IGNORECASE).strip()
    if not position:
        return None

    def normalize_date(value: str) -> str:
        return re.sub(r"(\d{4})\s*-?\s*yil", r"\1-yil", value.strip())

    period = f"{normalize_date(match.group('start'))} – {normalize_date(match.group('end'))}"
    return f"{period} | {workplace} | {position}"


def next_step(current_key: str, document_type: str = "cv") -> Step | None:
    steps = steps_for(document_type)
    for index, step in enumerate(steps):
        if step.key == current_key:
            return steps[index + 1] if index + 1 < len(steps) else None
    return steps[0]


def previous_step(current_key: str, document_type: str = "cv") -> Step | None:
    steps = steps_for(document_type)
    for index, step in enumerate(steps):
        if step.key == current_key:
            return steps[index - 1] if index > 0 else None
    return None


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
    if step.key == "objective_relative_birth":
        date_part, separator, place = clean.partition(",")
        try:
            datetime.strptime(date_part.strip(), "%d.%m.%Y")
        except ValueError:
            return text("invalid_relative_birth", language)
        if not separator or not place.strip():
            return text("invalid_relative_birth", language)
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
