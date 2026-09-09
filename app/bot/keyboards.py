from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

from app.core.config import get_settings
from app.services.localization import OBJECTIVE_LABELS, PREVIEW_LABELS, Language, normalize_language
from app.services.resume_flow import STEP_BY_KEY, steps_for


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O‘zbekcha", callback_data="language:uz"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="language:en"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="language:ru"),
            ]
        ]
    )


def document_type_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    labels: dict[Language, tuple[str, str, str, str]] = {
        "uz": ("📄 CV / Rezyume", "🪪 Obyektivka", "✍️ Tavsiyanoma", "🌐 Portfolio"),
        "en": ("📄 CV / Resume", "🪪 Personal sheet", "✍️ Recommendation", "🌐 Portfolio"),
        "ru": ("📄 CV / Резюме", "🪪 Объективка", "✍️ Рекомендация", "🌐 Портфолио"),
    }
    cv, objective, recommendation, portfolio = labels[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cv, callback_data="document:cv")],
            [InlineKeyboardButton(text=objective, callback_data="document:objective")],
            [InlineKeyboardButton(text=recommendation, callback_data="document:recommendation")],
            [InlineKeyboardButton(text=portfolio, callback_data="document:portfolio")],
        ]
    )


def _portfolio_back_label(language: str) -> str:
    return {
        "uz": "⬅️ Ortga",
        "en": "⬅️ Back",
        "ru": "⬅️ Назад",
    }[normalize_language(language)]


def portfolio_template_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    labels = ("◻️ Minimal", "✨ Modern", "🎨 Creative", "💻 Developer")
    codes = ("minimal", "modern", "creative", "developer")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"portfolio-template:{code}")]
            for code, label in zip(codes, labels, strict=True)
        ]
        + [
            [
                InlineKeyboardButton(
                    text=_portfolio_back_label(language), callback_data="portfolio:back:example"
                )
            ]
        ]
    )


def portfolio_sections_keyboard(
    language: str = "uz", selected: list[str] | None = None
) -> InlineKeyboardMarkup:
    selected_set = set(selected or [])
    labels = {
        "uz": (
            ("profile", "👤 Profil"),
            ("about", "📝 Men haqimda"),
            ("skills", "🛠 Ko‘nikmalar"),
            ("experience", "💼 Ish tajribasi"),
            ("education", "🎓 Ta’lim"),
            ("projects", "🚀 Loyihalar"),
            ("certificates", "🏅 Sertifikatlar"),
            ("publications", "📚 Nashrlar"),
            ("languages", "🌐 Tillar"),
            ("achievements", "🏆 Yutuqlar / Vlog"),
            ("links", "🔗 Havolalar va profillar"),
            ("contact", "📬 Kontakt"),
        ),
        "en": (
            ("profile", "👤 Profile"),
            ("about", "📝 About"),
            ("skills", "🛠 Skills"),
            ("experience", "💼 Experience"),
            ("education", "🎓 Education"),
            ("projects", "🚀 Projects"),
            ("certificates", "🏅 Certificates"),
            ("publications", "📚 Publications"),
            ("languages", "🌐 Languages"),
            ("achievements", "🏆 Achievements / Vlog"),
            ("links", "🔗 Links & Profiles"),
            ("contact", "📬 Contact"),
        ),
        "ru": (
            ("profile", "👤 Профиль"),
            ("about", "📝 Обо мне"),
            ("skills", "🛠 Навыки"),
            ("experience", "💼 Опыт"),
            ("education", "🎓 Образование"),
            ("projects", "🚀 Проекты"),
            ("certificates", "🏅 Сертификаты"),
            ("publications", "📚 Публикации"),
            ("languages", "🌐 Языки"),
            ("achievements", "🏆 Достижения / Влог"),
            ("links", "🔗 Ссылки и профили"),
            ("contact", "📬 Контакты"),
        ),
    }[normalize_language(language)]
    rows = [
        [
            InlineKeyboardButton(
                text=("✅ " if code in selected_set else "⬜ ") + label,
                callback_data=f"portfolio-section:{code}",
            )
        ]
        for code, label in labels
    ]
    start = {
        "uz": "➡️ To‘ldirishni boshlash",
        "en": "➡️ Start filling",
        "ru": "➡️ Начать заполнение",
    }[normalize_language(language)]
    rows.append([InlineKeyboardButton(text=start, callback_data="portfolio:start")])
    rows.append(
        [
            InlineKeyboardButton(
                text=_portfolio_back_label(language), callback_data="portfolio:back:templates"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def portfolio_ready_keyboard(language: str = "uz", example_url: str = "") -> InlineKeyboardMarkup:
    labels = {
        "uz": ("✅ Ha, boshlaymiz", "🔁 Namunani qayta ko‘rish"),
        "en": ("✅ Yes, start", "🔁 Show example again"),
        "ru": ("✅ Да, начать", "🔁 Показать пример"),
    }[normalize_language(language)]
    rows = [
        [InlineKeyboardButton(text=labels[0], callback_data="portfolio-ready:yes")],
        [InlineKeyboardButton(text=labels[1], callback_data="portfolio-ready:again")],
    ]
    if example_url:
        view_label = {
            "uz": "🌐 To‘liq namunani saytda ko‘rish",
            "en": "🌐 View the full example website",
            "ru": "🌐 Посмотреть полный пример на сайте",
        }[normalize_language(language)]
        rows.insert(0, [InlineKeyboardButton(text=view_label, url=example_url)])
    rows.append(
        [
            InlineKeyboardButton(
                text=_portfolio_back_label(language), callback_data="portfolio:back:documents"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def portfolio_step_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_portfolio_back_label(language), callback_data="portfolio:back:section"
                )
            ]
        ]
    )


def portfolio_review_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    rows = list(review_keyboard(language).inline_keyboard)
    rows.insert(
        0,
        [
            InlineKeyboardButton(
                text=_portfolio_back_label(language), callback_data="portfolio:back:last"
            )
        ],
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def portfolio_token_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_portfolio_back_label(language), callback_data="portfolio:back:review"
                )
            ]
        ]
    )


def cv_template_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    back = {"uz": "⬅️ Ortga", "en": "⬅️ Back", "ru": "⬅️ Назад"}[locale]
    webapp_url = get_settings().template_webapp_url.strip()
    if webapp_url:
        open_gallery = {
            "uz": "🎨 Shablonlarni ko‘rish va tanlash",
            "en": "🎨 View and choose a template",
            "ru": "🎨 Посмотреть и выбрать шаблон",
        }[locale]
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=open_gallery,
                        web_app=WebAppInfo(url=webapp_url),
                    )
                ],
                [InlineKeyboardButton(text=back, callback_data="document:choose")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📘 Classic", callback_data="template-family:classic")],
            [InlineKeyboardButton(text="✨ Modern", callback_data="template-family:modern")],
            [InlineKeyboardButton(text="🇪🇺 Europass", callback_data="template-family:europass")],
            [InlineKeyboardButton(text=back, callback_data="document:choose")],
        ]
    )


def europass_template_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    labels = {
        "uz": ("Europass 1", "Europass 2", "Europass 3", "⬅️ Shablonlarga qaytish"),
        "en": ("Europass 1", "Europass 2", "Europass 3", "⬅️ Back to templates"),
        "ru": ("Europass 1", "Europass 2", "Europass 3", "⬅️ К шаблонам"),
    }[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🔗 {labels[0]}", callback_data="template:europass_1")],
            [InlineKeyboardButton(text=f"🔗 {labels[1]}", callback_data="template:europass_2")],
            [InlineKeyboardButton(text=f"🔗 {labels[2]}", callback_data="template:europass_3")],
            [InlineKeyboardButton(text=labels[3], callback_data="document:cv")],
        ]
    )


def template_variant_keyboard(family: str, language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    family_names = {
        "classic": "Classic",
        "modern": {"uz": "Zamonaviy", "en": "Modern", "ru": "Современный"}[locale],
        "europass": "Europass",
    }
    selected_family = family if family in family_names else "classic"
    back = {"uz": "⬅️ Turlarga qaytish", "en": "⬅️ Back to styles", "ru": "⬅️ К стилям"}[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{family_names[selected_family]} {number}",
                    callback_data=f"template:{selected_family}_{number}",
                )
            ]
            for number in range(1, 4)
        ]
        + [[InlineKeyboardButton(text=back, callback_data="document:cv")]]
    )


def output_format_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📕 PDF", callback_data="format:pdf")],
            [InlineKeyboardButton(text="📘 Word (DOCX)", callback_data="format:docx")],
        ]
    )


def objective_education_level_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    choices: dict[Language, tuple[tuple[str, str], ...]] = {
        "uz": (
            ("higher", "Oliy"),
            ("incomplete_higher", "Tugallanmagan oliy"),
            ("secondary_special", "O‘rta maxsus"),
            ("secondary", "O‘rta"),
        ),
        "en": (
            ("higher", "Higher education"),
            ("incomplete_higher", "Incomplete higher"),
            ("secondary_special", "Specialized secondary"),
            ("secondary", "Secondary"),
        ),
        "ru": (
            ("higher", "Высшее"),
            ("incomplete_higher", "Незаконченное высшее"),
            ("secondary_special", "Среднее специальное"),
            ("secondary", "Среднее"),
        ),
    }
    back = {"uz": "⬅️ Orqaga", "en": "⬅️ Back", "ru": "⬅️ Назад"}[locale]
    rows = [
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f"objective-education:{code}",
            )
        ]
        for code, label in choices[locale]
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text=back,
                callback_data="flow:back:objective_education_level",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


QUESTION_EXAMPLES: dict[str, dict[Language, str]] = {
    "full_name": {
        "uz": "Dilnura Hamdamova",
        "en": "Dilnura Hamdamova",
        "ru": "Дилнура Хамдамова",
    },
    "job_title": {
        "uz": "Backend dasturchi",
        "en": "Backend Developer",
        "ru": "Backend-разработчик",
    },
    "phone": {
        "uz": "+998 90 123 45 67",
        "en": "+998 90 123 45 67",
        "ru": "+998 90 123 45 67",
    },
    "email": {
        "uz": "dilnura@example.com",
        "en": "dilnura@example.com",
        "ru": "dilnura@example.com",
    },
    "location": {"uz": "Toshkent", "en": "Tashkent", "ru": "Ташкент"},
    "summary": {
        "uz": "3 yillik tajribaga ega Java dasturchiman",
        "en": "Java developer with 3 years of experience",
        "ru": "Java-разработчик с опытом 3 года",
    },
    "skills": {"uz": "Java", "en": "Java", "ru": "Java"},
    "experience": {
        "uz": "2023–hozir — Example MCHJ, Java dasturchi",
        "en": "2023–present — Example LLC, Java Developer",
        "ru": "2023–н.в. — Example, Java-разработчик",
    },
    "education": {
        "uz": "2021–2025 — TDIU, Xalqaro iqtisodiyot",
        "en": "2021–2025 — TSUE, International Economics",
        "ru": "2021–2025 — ТГЭУ, Международная экономика",
    },
    "languages": {
        "uz": "Ingliz tili — B2",
        "en": "English — B2",
        "ru": "Английский — B2",
    },
    "objective_full_name": {
        "uz": "Abdullayev Botir Bahodirovich",
        "en": "Botir Abdullayev Bahodirovich",
        "ru": "Абдуллаев Ботир Баходирович",
    },
    "objective_position": {
        "uz": "Dasturchi",
        "en": "Software Developer",
        "ru": "Программист",
    },
    "objective_birth_date": {
        "uz": "20.08.1985",
        "en": "20.08.1985",
        "ru": "20.08.1985",
    },
    "objective_birth_place": {
        "uz": "Sirdaryo viloyati, Guliston shahri",
        "en": "Gulistan, Syrdarya region",
        "ru": "г. Гулистан, Сырдарьинская область",
    },
    "objective_nationality": {"uz": "o‘zbek", "en": "Uzbek", "ru": "узбек"},
    "objective_party": {"uz": "yo‘q", "en": "none", "ru": "нет"},
    "objective_education_level": {"uz": "Oliy", "en": "Higher education", "ru": "Высшее"},
    "objective_graduated": {
        "uz": "TDIU, 2021–2025",
        "en": "TSUE, 2021–2025",
        "ru": "ТГЭУ, 2021–2025",
    },
    "objective_specialty": {
        "uz": "Xalqaro iqtisodiyot",
        "en": "International Economics",
        "ru": "Международная экономика",
    },
    "objective_degree": {
        "uz": "iqtisodiyot fanlari nomzodi yoki yo‘q",
        "en": "PhD in Economics or none",
        "ru": "кандидат экономических наук или нет",
    },
    "objective_title": {
        "uz": "dotsent yoki yo‘q",
        "en": "Associate Professor or none",
        "ru": "доцент или нет",
    },
    "objective_languages": {
        "uz": "Ingliz tili — B2",
        "en": "English — B2",
        "ru": "Английский — B2",
    },
    "objective_awards": {
        "uz": "«Do‘stlik» ordeni yoki yo‘q",
        "en": "State award name or none",
        "ru": "Название госнаграды или нет",
    },
    "objective_elected": {
        "uz": "Tuman Kengashi deputati yoki yo‘q",
        "en": "District council member or none",
        "ru": "Депутат районного Кенгаша или нет",
    },
    "objective_employment": {
        "uz": "2021–hozir | TDIU | fakultet dekani",
        "en": "2021–present | TSUE | Faculty Dean",
        "ru": "2021–н.в. | ТГЭУ | декан факультета",
    },
    "objective_relative_name": {
        "uz": "Karimov Ali Valiyevich",
        "en": "Ali Karimov",
        "ru": "Каримов Али Валиевич",
    },
    "objective_relative_birth": {
        "uz": "20.03.1965, Toshkent shahri",
        "en": "20.03.1965, Tashkent",
        "ru": "20.03.1965, Ташкент",
    },
    "objective_relative_work": {
        "uz": "TDIU, professor",
        "en": "TSUE, professor",
        "ru": "ТГЭУ, профессор",
    },
    "objective_relative_address": {
        "uz": "Toshkent shahri, Chilonzor tumani",
        "en": "Tashkent, Chilanzar district",
        "ru": "Ташкент, Чиланзарский район",
    },
}

SKILL_SUGGESTION_VALUES: dict[str, str] = {
    "java": "Java",
    "spring": "Spring Boot",
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "docker": "Docker",
    "git": "Git",
    "rest": "REST API",
    "figma": "Figma",
    "ux": "UX Research",
    "prototyping": "Prototyping",
    "design_systems": "Design Systems",
    "excel": "Microsoft Excel",
    "accounting": "Buxgalteriya",
    "communication": "Communication",
    "project_management": "Project Management",
}


def suggested_skill_codes(job_title: str) -> tuple[str, ...]:
    title = job_title.lower()
    if any(word in title for word in ("java", "backend", "dasturchi", "developer", "programmer")):
        return ("java", "spring", "sql", "postgresql", "docker", "git", "rest")
    if any(word in title for word in ("designer", "dizayn", "ux", "ui")):
        return ("figma", "ux", "prototyping", "design_systems", "git")
    if any(word in title for word in ("buxgalter", "accountant", "finance")):
        return ("excel", "accounting", "communication")
    if any(word in title for word in ("manager", "menejer", "rahbar")):
        return ("project_management", "communication", "excel", "git")
    return ("communication", "project_management", "git")


def skill_suggestions_keyboard(job_title: str, language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    labels = {
        "uz": "💡 Tavsiya: ",
        "en": "💡 Suggested: ",
        "ru": "💡 Совет: ",
    }
    rows = [
        [
            InlineKeyboardButton(
                text=f"{labels[locale]}{SKILL_SUGGESTION_VALUES[code]}",
                callback_data=f"skill:suggest:{code}",
            )
        ]
        for code in suggested_skill_codes(job_title)
    ]
    rows.extend(question_navigation_keyboard("skills", locale).inline_keyboard)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def question_navigation_keyboard(step_key: str, language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    labels: dict[Language, tuple[str, str]] = {
        "uz": ("⬅️ Orqaga", "⏭ O‘tkazib yuborish"),
        "en": ("⬅️ Back", "⏭ Skip"),
        "ru": ("⬅️ Назад", "⏭ Пропустить"),
    }
    back_label, skip_label = labels[locale]
    rows = []
    navigation = [InlineKeyboardButton(text=back_label, callback_data=f"flow:back:{step_key}")]
    step = STEP_BY_KEY.get(step_key)
    if step is None or step.optional:
        navigation.append(
            InlineKeyboardButton(text=skip_label, callback_data=f"flow:skip:{step_key}")
        )
    rows.append(navigation)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def education_more_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    labels = {
        "uz": ("➕ Yana ta’lim qo‘shish", "✅ Davom etish", "⬅️ Orqaga"),
        "en": ("➕ Add education", "✅ Continue", "⬅️ Back"),
        "ru": ("➕ Добавить образование", "✅ Продолжить", "⬅️ Назад"),
    }[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=labels[0], callback_data="education:add")],
            [InlineKeyboardButton(text=labels[1], callback_data="education:done")],
            [InlineKeyboardButton(text=labels[2], callback_data="flow:back")],
        ]
    )


RELATIVE_LABELS: dict[Language, dict[str, str]] = {
    "uz": {
        "father": "Otasi",
        "mother": "Onasi",
        "older_brother": "Akasi",
        "younger_brother": "Ukasi",
        "older_sister": "Opasi",
        "younger_sister": "Singlisi",
    },
    "en": {
        "father": "Father",
        "mother": "Mother",
        "older_brother": "Older brother",
        "younger_brother": "Younger brother",
        "older_sister": "Older sister",
        "younger_sister": "Younger sister",
    },
    "ru": {
        "father": "Отец",
        "mother": "Мать",
        "older_brother": "Старший брат",
        "younger_brother": "Младший брат",
        "older_sister": "Старшая сестра",
        "younger_sister": "Младшая сестра",
    },
}


def relative_label(code: str, language: str = "uz") -> str:
    return RELATIVE_LABELS[normalize_language(language)].get(code, code)


def relatives_keyboard(selected: list[str], language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    buttons = []
    for code, label in RELATIVE_LABELS[locale].items():
        marker = "✅" if code in selected else "☑️"
        buttons.append(
            InlineKeyboardButton(text=f"{marker} {label}", callback_data=f"relative:toggle:{code}")
        )
    rows = [buttons[index : index + 2] for index in range(0, len(buttons), 2)]
    done = {"uz": "✅ Davom etish", "en": "✅ Continue", "ru": "✅ Продолжить"}[locale]
    none = {"uz": "⏭ Qarindosh yo‘q", "en": "⏭ None", "ru": "⏭ Нет"}[locale]
    back = {"uz": "⬅️ Orqaga", "en": "⬅️ Back", "ru": "⬅️ Назад"}[locale]
    rows.extend(
        [
            [InlineKeyboardButton(text=done, callback_data="relative:types:done")],
            [InlineKeyboardButton(text=none, callback_data="relative:types:none")],
            [InlineKeyboardButton(text=back, callback_data="flow:back:objective_relatives")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def relative_more_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    add = {"uz": "➕ Yana qo‘shish", "en": "➕ Add another", "ru": "➕ Добавить ещё"}[locale]
    proceed = {"uz": "✅ Keyingisiga o‘tish", "en": "✅ Next relative", "ru": "✅ Следующий"}[
        locale
    ]
    back = {"uz": "⬅️ Orqaga", "en": "⬅️ Back", "ru": "⬅️ Назад"}[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=add, callback_data="relative:add_same")],
            [InlineKeyboardButton(text=proceed, callback_data="relative:next")],
            [InlineKeyboardButton(text=back, callback_data="flow:back")],
        ]
    )


def photo_navigation_keyboard(
    language: str = "uz", document_type: str = "cv"
) -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    if document_type == "cv":
        skip_label = {
            "uz": "⏭ Rasmsiz davom etish",
            "en": "⏭ Continue without photo",
            "ru": "⏭ Продолжить без фото",
        }[locale]
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=skip_label, callback_data="photo:skip")]]
        )
    label = {
        "uz": "⬅️ Orqaga",
        "en": "⬅️ Back",
        "ru": "⬅️ Назад",
    }[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data="document:choose")]]
    )


def add_more_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    labels: dict[Language, tuple[str, str, str]] = {
        "uz": ("➕ Yana qo‘shish", "✅ Davom etish", "⬅️ Orqaga"),
        "en": ("➕ Add another", "✅ Continue", "⬅️ Back"),
        "ru": ("➕ Добавить ещё", "✅ Продолжить", "⬅️ Назад"),
    }
    add_label, continue_label, back_label = labels[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=add_label, callback_data="list:add")],
            [InlineKeyboardButton(text=continue_label, callback_data="list:done")],
            [InlineKeyboardButton(text=back_label, callback_data="flow:back")],
        ]
    )


def section_cancel_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    label = {"uz": "⬅️ Orqaga", "en": "⬅️ Back", "ru": "⬅️ Назад"}[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data="section:cancel")]]
    )


def start_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    labels: dict[Language, tuple[str, str]] = {
        "uz": ("📝 Yangi hujjat yaratish", "📂 Oxirgi hujjat"),
        "en": ("📝 Create a new document", "📂 Latest document"),
        "ru": ("📝 Создать новый документ", "📂 Последний документ"),
    }
    create_label, latest_label = labels[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=create_label, callback_data="resume:new")],
            [InlineKeyboardButton(text=latest_label, callback_data="resume:last")],
        ]
    )


def review_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    labels: dict[Language, tuple[str, str, str, str, str]] = {
        "uz": (
            "✅ Tasdiqlash",
            "✏️ O‘zgartirish",
            "➕ Bo‘lim qo‘shish",
            "➖ Bo‘limni o‘chirish",
            "🔄 Boshidan boshlash",
        ),
        "en": (
            "✅ Approve",
            "✏️ Edit",
            "➕ Add section",
            "➖ Remove section",
            "🔄 Start over",
        ),
        "ru": (
            "✅ Подтвердить",
            "✏️ Изменить",
            "➕ Добавить раздел",
            "➖ Удалить раздел",
            "🔄 Начать заново",
        ),
    }
    approve, edit, add_section, remove_section, restart = labels[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=approve, callback_data="resume:approve")],
            [InlineKeyboardButton(text=edit, callback_data="resume:edit")],
            [InlineKeyboardButton(text=add_section, callback_data="section:add")],
            [InlineKeyboardButton(text=remove_section, callback_data="section:remove")],
            [InlineKeyboardButton(text=restart, callback_data="resume:new")],
        ]
    )


def edit_fields_keyboard(language: str = "uz", document_type: str = "cv") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    labels: dict[Language, dict[str, str]] = {
        "uz": {
            "full_name": "Ism",
            "job_title": "Lavozim",
            "phone": "Telefon",
            "email": "Email",
            "location": "Manzil",
            "summary": "Profil",
            "skills": "Ko‘nikmalar",
            "experience": "Tajriba",
            "education": "Ta’lim",
            "languages": "Tillar",
            "back": "⬅️ Ortga",
        },
        "en": {
            "full_name": "Name",
            "job_title": "Position",
            "phone": "Phone",
            "email": "Email",
            "location": "Location",
            "summary": "Profile",
            "skills": "Skills",
            "experience": "Experience",
            "education": "Education",
            "languages": "Languages",
            "back": "⬅️ Back",
        },
        "ru": {
            "full_name": "Имя",
            "job_title": "Должность",
            "phone": "Телефон",
            "email": "Email",
            "location": "Адрес",
            "summary": "Профиль",
            "skills": "Навыки",
            "experience": "Опыт",
            "education": "Образование",
            "languages": "Языки",
            "back": "⬅️ Назад",
        },
    }
    if document_type == "objective":
        objective_key_labels = {
            "objective_full_name": "relative_name",
            "objective_position": "position",
            "objective_birth_date": "birth_date",
            "objective_birth_place": "birth_place",
            "objective_nationality": "nationality",
            "objective_party": "party",
            "objective_education_level": "education_level",
            "objective_graduated": "graduated",
            "objective_specialty": "specialty",
            "objective_degree": "degree",
            "objective_title": "academic_title",
            "objective_languages": "foreign_languages",
            "objective_awards": "awards",
            "objective_elected": "elected",
            "objective_employment": "employment",
            "objective_relatives": "relatives",
        }
        buttons = [
            InlineKeyboardButton(
                text=OBJECTIVE_LABELS[locale][objective_key_labels[step.key]],
                callback_data=f"resume:field:{step.key}",
            )
            for step in steps_for(document_type)
        ]
    else:
        buttons = [
            InlineKeyboardButton(
                text=labels[locale][step.key], callback_data=f"resume:field:{step.key}"
            )
            for step in steps_for(document_type)
        ]
    rows = [buttons[index : index + 2] for index in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton(text=labels[locale]["back"], callback_data="resume:last")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def remove_section_keyboard(data: dict[str, object], language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    document_type = str(data.get("document_type", "cv"))
    objective_key_labels = {
        "objective_position": "position",
        "objective_birth_date": "birth_date",
        "objective_birth_place": "birth_place",
        "objective_nationality": "nationality",
        "objective_party": "party",
        "objective_education_level": "education_level",
        "objective_graduated": "graduated",
        "objective_specialty": "specialty",
        "objective_degree": "degree",
        "objective_title": "academic_title",
        "objective_languages": "foreign_languages",
        "objective_awards": "awards",
        "objective_elected": "elected",
        "objective_employment": "employment",
        "objective_relatives": "relatives",
    }
    cv_keys = (
        "job_title",
        "phone",
        "email",
        "location",
        "summary",
        "skills",
        "experience",
        "education",
        "languages",
    )
    rows: list[list[InlineKeyboardButton]] = []
    if document_type == "objective":
        for key, label_key in objective_key_labels.items():
            if key in data:
                rows.append(
                    [
                        InlineKeyboardButton(
                            text=OBJECTIVE_LABELS[locale][label_key],
                            callback_data=f"section:delete:{key}",
                        )
                    ]
                )
    else:
        for key in cv_keys:
            if key in data:
                rows.append(
                    [
                        InlineKeyboardButton(
                            text=PREVIEW_LABELS[locale][key],
                            callback_data=f"section:delete:{key}",
                        )
                    ]
                )
    raw_custom = data.get("custom_sections", [])
    if isinstance(raw_custom, list):
        for index, item in enumerate(raw_custom):
            if isinstance(item, dict) and item.get("title"):
                rows.append(
                    [
                        InlineKeyboardButton(
                            text=str(item["title"]),
                            callback_data=f"section:delete:custom_{index}",
                        )
                    ]
                )
    back_label = {"uz": "⬅️ Orqaga", "en": "⬅️ Back", "ru": "⬅️ Назад"}[locale]
    rows.append([InlineKeyboardButton(text=back_label, callback_data="resume:last")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def delete_confirmation_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    labels: dict[Language, tuple[str, str]] = {
        "uz": ("Ha, o‘chirish", "Bekor qilish"),
        "en": ("Yes, delete", "Cancel"),
        "ru": ("Да, удалить", "Отмена"),
    }
    delete_label, cancel_label = labels[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=delete_label, callback_data="privacy:delete")],
            [InlineKeyboardButton(text=cancel_label, callback_data="privacy:cancel")],
        ]
    )
