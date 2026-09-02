from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.localization import OBJECTIVE_LABELS, PREVIEW_LABELS, Language, normalize_language
from app.services.resume_flow import steps_for


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


def cv_template_keyboard(language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    back = {"uz": "⬅️ Ortga", "en": "⬅️ Back", "ru": "⬅️ Назад"}[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📘 Classic", callback_data="template:classic")],
            [InlineKeyboardButton(text="✨ Modern", callback_data="template:modern")],
            [InlineKeyboardButton(text="🇪🇺 Europass", callback_data="template:europass")],
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


def output_format_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📕 PDF", callback_data="format:pdf")],
            [InlineKeyboardButton(text="📘 Word (DOCX)", callback_data="format:docx")],
        ]
    )


def question_navigation_keyboard(step_key: str, language: str = "uz") -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    labels: dict[Language, tuple[str, str]] = {
        "uz": ("⬅️ Orqaga", "⏭ O‘tkazib yuborish"),
        "en": ("⬅️ Back", "⏭ Skip"),
        "ru": ("⬅️ Назад", "⏭ Пропустить"),
    }
    back_label, skip_label = labels[locale]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=back_label, callback_data=f"flow:back:{step_key}"),
                InlineKeyboardButton(text=skip_label, callback_data=f"flow:skip:{step_key}"),
            ]
        ]
    )


def photo_navigation_keyboard(
    language: str = "uz", document_type: str = "cv"
) -> InlineKeyboardMarkup:
    locale = normalize_language(language)
    label = {
        "uz": "⬅️ Shablonlarga qaytish" if document_type == "cv" else "⬅️ Orqaga",
        "en": "⬅️ Back to templates" if document_type == "cv" else "⬅️ Back",
        "ru": "⬅️ К шаблонам" if document_type == "cv" else "⬅️ Назад",
    }[locale]
    callback_data = "document:cv" if document_type == "cv" else "document:choose"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data=callback_data)]]
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
