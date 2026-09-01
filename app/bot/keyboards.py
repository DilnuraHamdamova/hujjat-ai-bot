from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.resume_flow import STEPS


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Yangi CV yaratish", callback_data="resume:new")],
            [InlineKeyboardButton(text="📂 Oxirgi CV", callback_data="resume:last")],
        ]
    )


def review_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="resume:approve")],
            [InlineKeyboardButton(text="✏️ O‘zgartirish", callback_data="resume:edit")],
            [InlineKeyboardButton(text="🔄 Boshidan boshlash", callback_data="resume:new")],
        ]
    )


def edit_fields_keyboard() -> InlineKeyboardMarkup:
    labels = {
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
    }
    buttons = [
        InlineKeyboardButton(text=labels[step.key], callback_data=f"resume:field:{step.key}")
        for step in STEPS
    ]
    rows = [buttons[index : index + 2] for index in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="resume:last")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def delete_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ha, o‘chirish", callback_data="privacy:delete")],
            [InlineKeyboardButton(text="Bekor qilish", callback_data="privacy:cancel")],
        ]
    )
