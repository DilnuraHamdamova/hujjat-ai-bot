from typing import Literal

Language = Literal["uz", "en", "ru"]

SUPPORTED_LANGUAGES: tuple[Language, ...] = ("uz", "en", "ru")


def normalize_language(language: str | None) -> Language:
    code = (language or "uz").lower().split("-", 1)[0]
    return code if code in SUPPORTED_LANGUAGES else "uz"


TEXTS: dict[str, dict[Language, str]] = {
    "choose_language": {
        "uz": "Tilni tanlang / Choose a language / Выберите язык:",
        "en": "Tilni tanlang / Choose a language / Выберите язык:",
        "ru": "Tilni tanlang / Choose a language / Выберите язык:",
    },
    "welcome": {
        "uz": (
            "<b>Assalomu alaykum! Hujjat tayyorlab beruvchi botga xush kelibsiz!</b>\n\n"
            "Bu bot orqali rezyume, portfolio, obyektivka va tavsiyanoma "
            "yaratishingiz mumkin."
        ),
        "en": (
            "<b>Hello! Welcome to the document creation bot!</b>\n\n"
            "Here you can create a resume, portfolio, personal information sheet, "
            "and recommendation letter."
        ),
        "ru": (
            "<b>Здравствуйте! Добро пожаловать в бот для создания документов!</b>\n\n"
            "Здесь вы можете создать резюме, портфолио, объективку и рекомендательное письмо."
        ),
    },
    "choose_document": {
        "uz": "Nima tayyorlamoqchisiz?",
        "en": "What would you like to create?",
        "ru": "Что вы хотите создать?",
    },
    "choose_template": {
        "uz": "CV uchun shablonni tanlang:",
        "en": "Choose a resume template:",
        "ru": "Выберите шаблон резюме:",
    },
    "template_gallery_intro": {
        "uz": "Quyidagi shablon namunalarini ko‘rib, bittasini tanlang:",
        "en": "Review the template previews below and choose one:",
        "ru": "Посмотрите примеры шаблонов ниже и выберите один:",
    },
    "template_classic_caption": {
        "uz": "1. Classic — sodda va rasmiy",
        "en": "1. Classic — clean and formal",
        "ru": "1. Classic — простой и официальный",
    },
    "template_modern_caption": {
        "uz": "2. Modern — zamonaviy va rangli",
        "en": "2. Modern — contemporary and colorful",
        "ru": "2. Modern — современный и яркий",
    },
    "template_europass_caption": {
        "uz": "3. Europass — Yevropa uslubida",
        "en": "3. Europass — European-style layout",
        "ru": "3. Europass — в европейском стиле",
    },
    "coming_soon": {
        "uz": "Bu imkoniyat tez orada ishga tushadi.",
        "en": "This feature is coming soon.",
        "ru": "Эта функция скоро появится.",
    },
    "send_photo": {
        "uz": (
            "Obyektivka uchun 3×4 formatga mos, yuzingiz aniq ko‘rinadigan "
            "rasm yuboring. Rasm qo‘shish majburiy."
        ),
        "en": (
            "Send a clear portrait suitable for a 3×4 photo. "
            "A photo is required for the personal information sheet."
        ),
        "ru": (
            "Отправьте чёткую портретную фотографию формата 3×4. "
            "Фотография для объективки обязательна."
        ),
    },
    "photo_saved": {
        "uz": "✅ Rasm saqlandi.",
        "en": "✅ Photo saved.",
        "ru": "✅ Фотография сохранена.",
    },
    "photo_required": {
        "uz": "Avval rasmni foto ko‘rinishida yuboring.",
        "en": "Please send the photo first.",
        "ru": "Сначала отправьте фотографию.",
    },
    "section_title_prompt": {
        "uz": "Yangi bo‘lim nomini kiriting (masalan: Sertifikatlar):",
        "en": "Enter the new section title (for example: Certificates):",
        "ru": "Введите название нового раздела (например: Сертификаты):",
    },
    "section_content_prompt": {
        "uz": "Endi ushbu bo‘lim mazmunini kiriting:",
        "en": "Now enter the content of this section:",
        "ru": "Теперь введите содержание этого раздела:",
    },
    "choose_remove_section": {
        "uz": "O‘chirmoqchi bo‘lgan bo‘limni tanlang:",
        "en": "Choose the section you want to remove:",
        "ru": "Выберите раздел, который хотите удалить:",
    },
    "section_removed": {
        "uz": "✅ Bo‘lim o‘chirildi.",
        "en": "✅ Section removed.",
        "ru": "✅ Раздел удалён.",
    },
    "no_removable_sections": {
        "uz": "O‘chirish mumkin bo‘lgan bo‘lim yo‘q.",
        "en": "There are no removable sections.",
        "ru": "Нет разделов, которые можно удалить.",
    },
    "choose_format": {
        "uz": "Hujjatni qaysi formatda tayyorlaylik?",
        "en": "Which format should the document use?",
        "ru": "В каком формате подготовить документ?",
    },
    "add_more_question": {
        "uz": "✅ Saqlandi. Yana qo‘shasizmi?",
        "en": "✅ Saved. Would you like to add another?",
        "ru": "✅ Сохранено. Добавить ещё?",
    },
    "help": {
        "uz": (
            "<b>Buyruqlar</b>\n/start — asosiy menyu\n/new — yangi hujjat\n"
            "/my_cv — oxirgi hujjat\n/delete_me — barcha ma’lumotlarni o‘chirish"
        ),
        "en": (
            "<b>Commands</b>\n/start — main menu\n/new — new document\n"
            "/my_cv — latest document\n/delete_me — delete all my data"
        ),
        "ru": (
            "<b>Команды</b>\n/start — главное меню\n/new — новый документ\n"
            "/my_cv — последний документ\n/delete_me — удалить все мои данные"
        ),
    },
    "no_cv": {
        "uz": "Hali hujjat yaratilmagan.",
        "en": "No document has been created yet.",
        "ru": "Документ ещё не создан.",
    },
    "which_edit": {
        "uz": "Qaysi ma’lumotni o‘zgartirmoqchisiz?",
        "en": "Which information would you like to change?",
        "ru": "Какие данные вы хотите изменить?",
    },
    "invalid_field": {"uz": "Noto‘g‘ri maydon", "en": "Invalid field", "ru": "Неверное поле"},
    "cv_not_found": {"uz": "CV topilmadi", "en": "Resume not found", "ru": "Резюме не найдено"},
    "voice_disabled": {
        "uz": (
            "Ovozli xabar funksiyasi keyingi bosqichda ulanadi. "
            "Hozir javobni matn ko‘rinishida yuboring."
        ),
        "en": (
            "Voice messages will be enabled in a later update. "
            "Please send your answer as text for now."
        ),
        "ru": "Голосовые сообщения будут подключены позже. Пока отправьте ответ текстом.",
    },
    "start_first": {
        "uz": "Avval yangi CV yaratishni boshlang.",
        "en": "Start creating a new resume first.",
        "ru": "Сначала начните создание нового резюме.",
    },
    "broken_state": {
        "uz": "Jarayon holati buzilgan. /new orqali qayta boshlang.",
        "en": "The process state is invalid. Restart with /new.",
        "ru": "Состояние процесса нарушено. Начните заново командой /new.",
    },
    "approve_missing": {
        "uz": "Tasdiqlash uchun tayyor CV topilmadi",
        "en": "No resume is ready for approval",
        "ru": "Нет резюме, готового к подтверждению",
    },
    "preparing_alert": {
        "uz": "Hujjatlar tayyorlanmoqda...",
        "en": "Documents are being prepared...",
        "ru": "Документы готовятся...",
    },
    "preparing": {
        "uz": "⏳ {format} hujjati yaratilmoqda...",
        "en": "⏳ Creating the {format} document...",
        "ru": "⏳ Создаём документ в формате {format}...",
    },
    "file_ready": {
        "uz": "✅ {filename} tayyor",
        "en": "✅ {filename} is ready",
        "ru": "✅ {filename} готов",
    },
    "success": {
        "uz": "✅ Hujjat muvaffaqiyatli tayyorlandi.",
        "en": "✅ Your document has been created successfully.",
        "ru": "✅ Документ успешно создан.",
    },
    "generation_error": {
        "uz": "Hujjat yaratishda xatolik yuz berdi. Birozdan keyin qayta urinib ko‘ring.",
        "en": "An error occurred while creating the document. Please try again later.",
        "ru": "При создании документа произошла ошибка. Попробуйте позже.",
    },
    "delete_prompt": {
        "uz": "Barcha CV, hujjat va profilingiz o‘chirilsinmi? Bu amalni qaytarib bo‘lmaydi.",
        "en": "Delete all resumes, documents, and your profile? This action cannot be undone.",
        "ru": "Удалить все резюме, документы и ваш профиль? Это действие нельзя отменить.",
    },
    "cancelled": {"uz": "Bekor qilindi", "en": "Cancelled", "ru": "Отменено"},
    "data_kept": {
        "uz": "Ma’lumotlaringiz saqlab qolindi.",
        "en": "Your data has been kept.",
        "ru": "Ваши данные сохранены.",
    },
    "data_deleted_alert": {
        "uz": "Ma’lumotlar o‘chirildi",
        "en": "Data deleted",
        "ru": "Данные удалены",
    },
    "data_deleted": {
        "uz": "Barcha ma’lumotlaringiz o‘chirildi.",
        "en": "All your data has been deleted.",
        "ru": "Все ваши данные удалены.",
    },
    "empty_answer": {
        "uz": "Javob bo‘sh bo‘lmasligi kerak.",
        "en": "The answer cannot be empty.",
        "ru": "Ответ не может быть пустым.",
    },
    "long_answer": {
        "uz": "Javob juda uzun. 600 belgidan qisqaroq yozing.",
        "en": "The answer is too long. Use fewer than 600 characters.",
        "ru": "Ответ слишком длинный. Используйте менее 600 символов.",
    },
    "invalid_email": {
        "uz": "Email manzil noto‘g‘ri ko‘rinmoqda. Masalan: ali@example.com",
        "en": "The email address looks invalid. Example: ali@example.com",
        "ru": "Некорректный email. Пример: ali@example.com",
    },
    "invalid_phone": {
        "uz": "Telefon raqamini to‘liq kiriting. Masalan: +998 90 123 45 67",
        "en": "Enter the full phone number. Example: +998 90 123 45 67",
        "ru": "Введите полный номер телефона. Пример: +998 90 123 45 67",
    },
}


def text(key: str, language: str | None, **values: str) -> str:
    return TEXTS[key][normalize_language(language)].format(**values)


STEP_PROMPTS: dict[str, dict[Language, str]] = {
    "full_name": {
        "uz": "Ism va familiyangizni kiriting:",
        "en": "Enter your full name:",
        "ru": "Введите имя и фамилию:",
    },
    "job_title": {
        "uz": "Qaysi lavozim uchun CV tayyorlaymiz?",
        "en": "Which position is this resume for?",
        "ru": "Для какой должности готовим резюме?",
    },
    "phone": {
        "uz": "Telefon raqamingizni kiriting:",
        "en": "Enter your phone number:",
        "ru": "Введите номер телефона:",
    },
    "email": {
        "uz": "Email manzilingizni kiriting:",
        "en": "Enter your email address:",
        "ru": "Введите адрес электронной почты:",
    },
    "location": {
        "uz": "Yashash joyingizni kiriting (masalan, Toshkent):",
        "en": "Enter your location (for example, Tashkent):",
        "ru": "Укажите место проживания (например, Ташкент):",
    },
    "summary": {
        "uz": "O‘zingiz haqingizda qisqa professional ma’lumot yozing:",
        "en": "Write a short professional summary:",
        "ru": "Напишите краткое профессиональное описание:",
    },
    "skills": {
        "uz": "Bitta ko‘nikmangizni kiriting:",
        "en": "Enter one skill:",
        "ru": "Введите один навык:",
    },
    "experience": {
        "uz": "Bitta ish joyi va tajribangizni kiriting. Tajriba bo‘lmasa '-' yuboring:",
        "en": "Enter one workplace and experience entry. Send '-' if you have none:",
        "ru": "Введите одно место работы и опыт. Если опыта нет, отправьте '-':",
    },
    "education": {
        "uz": "Bitta ta’lim ma’lumotingizni kiriting:",
        "en": "Enter one education entry:",
        "ru": "Введите одну запись об образовании:",
    },
    "languages": {
        "uz": "Bitta til va darajasini kiriting (masalan: Ingliz — B2):",
        "en": "Enter one language and proficiency level (for example: English — C1):",
        "ru": "Введите один язык и уровень владения (например: Английский — B2):",
    },
    "objective_full_name": {
        "uz": "Familiya, ism va otangizning ismini to‘liq kiriting:",
        "en": "Enter your full name, including patronymic:",
        "ru": "Введите фамилию, имя и отчество полностью:",
    },
    "objective_position": {
        "uz": "Hozirgi ish joyingiz va lavozimingizni kiriting:",
        "en": "Enter your current workplace and position:",
        "ru": "Укажите текущее место работы и должность:",
    },
    "objective_birth_date": {
        "uz": "Tug‘ilgan sanangizni kiriting (kun.oy.yil):",
        "en": "Enter your date of birth (day.month.year):",
        "ru": "Введите дату рождения (день.месяц.год):",
    },
    "objective_birth_place": {
        "uz": "Tug‘ilgan joyingizni kiriting:",
        "en": "Enter your place of birth:",
        "ru": "Введите место рождения:",
    },
    "objective_nationality": {
        "uz": "Millatingizni kiriting:",
        "en": "Enter your nationality:",
        "ru": "Укажите национальность:",
    },
    "objective_party": {
        "uz": "Partiyaviyligingizni kiriting. A’zo bo‘lmasangiz '-' yuboring:",
        "en": "Enter your political party membership. Send '-' if none:",
        "ru": "Укажите партийность. Если не состоите в партии, отправьте '-':",
    },
    "objective_education_level": {
        "uz": "Ma’lumotingiz darajasini kiriting (masalan: oliy):",
        "en": "Enter your education level (for example: higher education):",
        "ru": "Укажите уровень образования (например: высшее):",
    },
    "objective_graduated": {
        "uz": "Bitta tamomlagan ta’lim muassasangizni yili bilan kiriting:",
        "en": "Enter one graduated institution with the year:",
        "ru": "Введите одно оконченное учебное заведение и год:",
    },
    "objective_specialty": {
        "uz": "Ma’lumotingiz bo‘yicha mutaxassisligingizni kiriting:",
        "en": "Enter your specialization by education:",
        "ru": "Укажите специальность по образованию:",
    },
    "objective_degree": {
        "uz": "Ilmiy darajangizni kiriting. Bo‘lmasa '-' yuboring:",
        "en": "Enter your academic degree. Send '-' if none:",
        "ru": "Укажите учёную степень. Если нет, отправьте '-':",
    },
    "objective_title": {
        "uz": "Ilmiy unvoningizni kiriting. Bo‘lmasa '-' yuboring:",
        "en": "Enter your academic title. Send '-' if none:",
        "ru": "Укажите учёное звание. Если нет, отправьте '-':",
    },
    "objective_languages": {
        "uz": "Bitta biladigan chet tilingizni kiriting:",
        "en": "Enter one foreign language you know:",
        "ru": "Введите один иностранный язык, которым владеете:",
    },
    "objective_awards": {
        "uz": "Davlat mukofotlaringizni kiriting. Bo‘lmasa '-' yuboring:",
        "en": "Enter your state awards. Send '-' if none:",
        "ru": "Укажите государственные награды. Если нет, отправьте '-':",
    },
    "objective_elected": {
        "uz": "Saylanadigan organlardagi a’zoligingizni kiriting. Bo‘lmasa '-' yuboring:",
        "en": "Enter membership in elected bodies. Send '-' if none:",
        "ru": "Укажите членство в выборных органах. Если нет, отправьте '-':",
    },
    "objective_employment": {
        "uz": "Mehnat faoliyatingizdagi bitta davrni kiriting:",
        "en": "Enter one period from your employment history:",
        "ru": "Введите один период трудовой деятельности:",
    },
    "objective_relatives": {
        "uz": (
            "Bitta yaqin qarindoshingizni quyidagicha yozing:\n"
            "Qarindoshligi | F.I.Sh. | tug‘ilgan yili va joyi | ish joyi va lavozimi | manzili"
        ),
        "en": (
            "Enter one close relative in this format:\n"
            "Relationship | Full name | birth year and place | workplace and position | address"
        ),
        "ru": (
            "Укажите одного близкого родственника в формате:\n"
            "Родство | Ф.И.О. | год и место рождения | место работы и должность | адрес"
        ),
    },
}


def step_prompt(key: str, language: str | None) -> str:
    return STEP_PROMPTS[key][normalize_language(language)]


PREVIEW_LABELS: dict[Language, dict[str, str]] = {
    "uz": {
        "title": "CV ma’lumotlarini tekshiring",
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
    },
    "en": {
        "title": "Review your resume information",
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
    },
    "ru": {
        "title": "Проверьте данные резюме",
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
    },
}


DOCUMENT_LABELS: dict[Language, dict[str, str]] = {
    "uz": {
        "profile": "PROFIL",
        "skills": "KO‘NIKMALAR",
        "experience": "ISH TAJRIBASI",
        "education": "TA’LIM",
        "languages": "TILLAR",
    },
    "en": {
        "profile": "PROFILE",
        "skills": "SKILLS",
        "experience": "WORK EXPERIENCE",
        "education": "EDUCATION",
        "languages": "LANGUAGES",
    },
    "ru": {
        "profile": "ПРОФИЛЬ",
        "skills": "НАВЫКИ",
        "experience": "ОПЫТ РАБОТЫ",
        "education": "ОБРАЗОВАНИЕ",
        "languages": "ЯЗЫКИ",
    },
}


OBJECTIVE_LABELS: dict[Language, dict[str, str]] = {
    "uz": {
        "document_title": "MA’LUMOTNOMA",
        "position": "Hozirgi ish joyi va lavozimi",
        "birth_date": "Tug‘ilgan sanasi",
        "birth_place": "Tug‘ilgan joyi",
        "nationality": "Millati",
        "party": "Partiyaviyligi",
        "education_level": "Ma’lumoti",
        "graduated": "Tamomlagan",
        "specialty": "Ma’lumoti bo‘yicha mutaxassisligi",
        "degree": "Ilmiy darajasi",
        "academic_title": "Ilmiy unvoni",
        "foreign_languages": "Qaysi chet tillarini biladi",
        "awards": "Davlat mukofotlari",
        "elected": "Saylanadigan organlardagi a’zoligi",
        "employment": "MEHNAT FAOLIYATI",
        "relatives": "YAQIN QARINDOSHLARI HAQIDA MA’LUMOT",
        "relationship": "Qarindoshligi",
        "relative_name": "Familiyasi, ismi va otasining ismi",
        "relative_birth": "Tug‘ilgan yili va joyi",
        "relative_work": "Ish joyi va lavozimi",
        "relative_address": "Turar joyi",
    },
    "en": {
        "document_title": "PERSONAL INFORMATION SHEET",
        "position": "Current workplace and position",
        "birth_date": "Date of birth",
        "birth_place": "Place of birth",
        "nationality": "Nationality",
        "party": "Political party membership",
        "education_level": "Education",
        "graduated": "Graduated from",
        "specialty": "Specialization by education",
        "degree": "Academic degree",
        "academic_title": "Academic title",
        "foreign_languages": "Foreign languages",
        "awards": "State awards",
        "elected": "Membership in elected bodies",
        "employment": "EMPLOYMENT HISTORY",
        "relatives": "INFORMATION ABOUT CLOSE RELATIVES",
        "relationship": "Relationship",
        "relative_name": "Full name",
        "relative_birth": "Birth year and place",
        "relative_work": "Workplace and position",
        "relative_address": "Address",
    },
    "ru": {
        "document_title": "ОБЪЕКТИВКА",
        "position": "Текущее место работы и должность",
        "birth_date": "Дата рождения",
        "birth_place": "Место рождения",
        "nationality": "Национальность",
        "party": "Партийность",
        "education_level": "Образование",
        "graduated": "Окончил(а)",
        "specialty": "Специальность по образованию",
        "degree": "Учёная степень",
        "academic_title": "Учёное звание",
        "foreign_languages": "Иностранные языки",
        "awards": "Государственные награды",
        "elected": "Членство в выборных органах",
        "employment": "ТРУДОВАЯ ДЕЯТЕЛЬНОСТЬ",
        "relatives": "СВЕДЕНИЯ О БЛИЗКИХ РОДСТВЕННИКАХ",
        "relationship": "Родство",
        "relative_name": "Фамилия, имя и отчество",
        "relative_birth": "Год и место рождения",
        "relative_work": "Место работы и должность",
        "relative_address": "Адрес",
    },
}
