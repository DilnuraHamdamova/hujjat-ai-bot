from typing import Literal

Language = Literal["uz", "en", "ru"]

SUPPORTED_LANGUAGES: tuple[Language, ...] = ("uz", "en", "ru")

PORTFOLIO_SECTION_LABELS: dict[Language, dict[str, str]] = {
    "uz": {
        "profile": "Profil",
        "about": "Men haqimda",
        "skills": "Ko‘nikmalar",
        "experience": "Ish tajribasi",
        "education": "Ta’lim",
        "projects": "Loyihalar",
        "certificates": "Sertifikatlar",
        "publications": "Nashrlar",
        "languages": "Tillar",
        "achievements": "Yutuqlar / Vlog",
        "links": "Havolalar va profillar",
        "contact": "Bog‘lanish",
    },
    "en": {
        "profile": "Profile",
        "about": "About",
        "skills": "Skills",
        "experience": "Experience",
        "education": "Education",
        "projects": "Projects",
        "certificates": "Certificates",
        "publications": "Publications",
        "languages": "Languages",
        "achievements": "Achievements / Vlog",
        "links": "Links & Profiles",
        "contact": "Contact",
    },
    "ru": {
        "profile": "Профиль",
        "about": "Обо мне",
        "skills": "Навыки",
        "experience": "Опыт работы",
        "education": "Образование",
        "projects": "Проекты",
        "certificates": "Сертификаты",
        "publications": "Публикации",
        "languages": "Языки",
        "achievements": "Достижения / Влог",
        "links": "Ссылки и профили",
        "contact": "Контакты",
    },
}

PORTFOLIO_SECTION_PROMPTS: dict[Language, dict[str, str]] = {
    "uz": {
        "profile": (
            "Profil: ism-familiya, kasbiy lavozim va qisqa shiorni alohida qatorlarda "
            "yozing."
        ),
        "about": "Men haqimda: tajriba, yo‘nalish va maqsadingizni 2–4 jumlada yozing.",
        "skills": "Ko‘nikmalar: asosiy ko‘nikmalaringizni vergul bilan ajrating.",
        "experience": (
            "Ish tajribasi: kompaniya, lavozim, davr va natijalarni yozing. Har bir ish "
            "joyini yangi qatordan boshlang."
        ),
        "education": "Ta’lim: muassasa, yo‘nalish va o‘qigan yillaringizni yozing.",
        "projects": (
            "Loyihalar: nomi, natijasi, texnologiyalar va GitHub yoki demo havolasini "
            "yozing."
        ),
        "certificates": "Sertifikatlar: nomi, bergan tashkilot, yil va havolasini yozing.",
        "publications": "Nashrlar: maqola yoki nashr nomi, qisqa tavsifi va havolasini yozing.",
        "languages": "Tillar: har bir til va darajani yozing (masalan: Ingliz tili — C1).",
        "achievements": "Yutuqlar / Vlog: nomi, natijasi va rasm yoki video havolasini yozing.",
        "links": (
            "Havolalar va profillar: GitHub, LinkedIn, Telegram yoki shaxsiy sayt "
            "havolalarini yozing."
        ),
        "contact": "Bog‘lanish: email, telefon va joylashuvingizni alohida qatorlarda yozing.",
    },
    "en": {
        "profile": (
            "Profile: enter your full name, professional title, and a short tagline on "
            "separate lines."
        ),
        "about": "About: describe your experience, focus, and goals in 2–4 sentences.",
        "skills": "Skills: separate your core skills with commas.",
        "experience": (
            "Experience: include company, role, dates, and outcomes. Start each position "
            "on a new line."
        ),
        "education": "Education: include the institution, field of study, and dates.",
        "projects": (
            "Projects: include the name, impact, technologies, and a GitHub or live-demo "
            "link."
        ),
        "certificates": "Certificates: include the credential, issuer, year, and link.",
        "publications": "Publications: include the title, a short description, and link.",
        "languages": (
            "Languages: enter each language and proficiency level (for example: "
            "English — C1)."
        ),
        "achievements": (
            "Achievements / Vlog: include the title, result, and an image or video link."
        ),
        "links": "Links & Profiles: add GitHub, LinkedIn, Telegram, or your personal website.",
        "contact": "Contact: enter your email, phone number, and location on separate lines.",
    },
    "ru": {
        "profile": "Профиль: укажите имя, профессию и короткий слоган на отдельных строках.",
        "about": "Обо мне: опишите опыт, специализацию и цели в 2–4 предложениях.",
        "skills": "Навыки: перечислите основные навыки через запятую.",
        "experience": (
            "Опыт работы: укажите компанию, должность, период и результаты. Каждое место "
            "работы начните с новой строки."
        ),
        "education": "Образование: укажите учебное заведение, специальность и годы обучения.",
        "projects": "Проекты: укажите название, результат, технологии и ссылку на GitHub или демо.",
        "certificates": "Сертификаты: укажите название, организацию, год и ссылку.",
        "publications": "Публикации: укажите название, краткое описание и ссылку.",
        "languages": "Языки: укажите каждый язык и уровень владения (например: Английский — C1).",
        "achievements": (
            "Достижения / Влог: укажите название, результат и ссылку на фото или видео."
        ),
        "links": "Ссылки и профили: добавьте GitHub, LinkedIn, Telegram или личный сайт.",
        "contact": "Контакты: укажите email, телефон и город на отдельных строках.",
    },
}


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
    "portfolio_example": {
        "uz": (
            "✨ <b>Professional loyiha menejeri portfolio namunasi</b>\n\n"
            "<b>Madina Karimova</b> — strategik loyiha menejeri.\n\n"
            "Profil · Men haqimda · Ko‘nikmalar · Ish tajribasi · Ta’lim\n"
            "Loyihalar · Sertifikatlar · Nashrlar · Tillar · Yutuqlar / Vlog\n"
            "Havolalar va profillar · Bog‘lanish\n\n"
            "Quyidagi tugma orqali to‘liq professional saytni ko‘ring."
        ),
        "en": (
            "✨ <b>Professional project manager portfolio example</b>\n\n"
            "<b>Madina Karimova</b> — a strategic project manager.\n\n"
            "Profile · About · Skills · Experience · Education · Projects\n"
            "Certificates · Publications · Languages · Achievements / Vlog\n"
            "Links &amp; Profiles · Contact\n\n"
            "Open the complete professional website with the button below."
        ),
        "ru": (
            "✨ <b>Пример профессионального портфолио менеджера проектов</b>\n\n"
            "<b>Madina Karimova</b> — менеджер проектов со стратегическим мышлением.\n\n"
            "Профиль · Обо мне · Навыки · Опыт работы · Образование · Проекты\n"
            "Сертификаты · Публикации · Языки · Достижения / Влог\n"
            "Ссылки и профили · Контакты\n\n"
            "Полный профессиональный сайт доступен по кнопке ниже."
        ),
    },
    "portfolio_choose_template": {
        "uz": "Endi portfolio dizaynini tanlang:",
        "en": "Now choose a portfolio design:",
        "ru": "Теперь выберите дизайн портфолио:",
    },
    "portfolio_ready_prompt": {
        "uz": "Namuna tushunarlimi? Portfolio yaratishni boshlaymizmi?",
        "en": "Is the example clear? Shall we start building your portfolio?",
        "ru": "Пример понятен? Начнём создавать ваше портфолио?",
    },
    "portfolio_sections_intro": {
        "uz": (
            "Portfolio uchun kerakli kategoriyalarni tanlang. Savollar professional "
            "tartibda navbatma-navbat beriladi:"
        ),
        "en": (
            "Choose the categories for your portfolio. Questions will follow in a "
            "professional order:"
        ),
        "ru": (
            "Выберите категории для портфолио. Вопросы будут заданы поочерёдно в "
            "профессиональном порядке:"
        ),
    },
    "portfolio_select_section": {
        "uz": "Avval kamida bitta kategoriya tanlang.",
        "en": "Select at least one category first.",
        "ru": "Сначала выберите хотя бы одну категорию.",
    },
    "portfolio_section_saved": {
        "uz": "✅ Bo‘lim saqlandi. Keyingi bo‘lim:\n\n{prompt}",
        "en": "✅ Section saved. Next section:\n\n{prompt}",
        "ru": "✅ Раздел сохранён. Следующий раздел:\n\n{prompt}",
    },
    "portfolio_token_prompt": {
        "uz": (
            "Netlify Personal Access Token yuboring. Token saqlanmaydi va faqat bir "
            "martalik joylash uchun ishlatiladi.\n\nTokenni Netlify → User settings → "
            "Applications → Personal access tokens bo‘limidan oling."
        ),
        "en": (
            "Send your Netlify Personal Access Token. It is not stored and is used only "
            "for this one-time deployment.\n\nGet it from Netlify → User settings → "
            "Applications → Personal access tokens."
        ),
        "ru": (
            "Отправьте Netlify Personal Access Token. Он не сохраняется и используется "
            "только для этой разовой публикации.\n\nПолучить токен можно в Netlify → User "
            "settings → Applications → Personal access tokens."
        ),
    },
    "portfolio_deploying": {
        "uz": "Portfolio Netlify’ga joylanmoqda…",
        "en": "Publishing your portfolio to Netlify…",
        "ru": "Публикуем портфолио на Netlify…",
    },
    "portfolio_deployed": {
        "uz": "✅ Portfolio tayyor va Netlify’ga joylandi:\n{url}",
        "en": "✅ Your portfolio is ready and live on Netlify:\n{url}",
        "ru": "✅ Портфолио готово и опубликовано на Netlify:\n{url}",
    },
    "portfolio_deploy_failed": {
        "uz": "❌ Portfolio joylanmadi. Tokenni tekshirib, qayta yuboring.",
        "en": "❌ The portfolio could not be published. Check the token and send it again.",
        "ru": "❌ Не удалось опубликовать портфолио. Проверьте токен и отправьте его снова.",
    },
    "choose_template": {
        "uz": "CV uchun shablonni tanlang:",
        "en": "Choose a resume template:",
        "ru": "Выберите шаблон резюме:",
    },
    "choose_europass_template": {
        "uz": "Europass modelini tanlang:",
        "en": "Choose a Europass design:",
        "ru": "Выберите дизайн Europass:",
    },
    "choose_template_variant": {
        "uz": "Ushbu turdagi 3 ta shablondan birini tanlang:",
        "en": "Choose one of the three templates in this style:",
        "ru": "Выберите один из трёх шаблонов этого стиля:",
    },
    "skill_suggestions_hint": {
        "uz": "Lavozimingizga mos ko‘nikmalar:",
        "en": "Skills suggested for your position:",
        "ru": "Навыки, рекомендованные для вашей должности:",
    },
    "template_selected": {
        "uz": "✅ Shablon tanlandi.",
        "en": "✅ Template selected.",
        "ru": "✅ Шаблон выбран.",
    },
    "template_gallery_intro": {
        "uz": "CV ko‘rinishini tanlang. Tayyor hujjat aynan tanlagan modelingizda yaratiladi:",
        "en": "Choose a resume style. Your document will be generated in the selected design:",
        "ru": "Выберите стиль резюме. Документ будет создан именно в выбранном дизайне:",
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
            "rasm yuboring. Rasm qo‘shish majburiy.\n"
            "Qo‘llab-quvvatlanadigan formatlar: JPG, JPEG yoki PNG."
        ),
        "en": (
            "Send a clear portrait suitable for a 3×4 photo. "
            "A photo is required for the personal information sheet.\n"
            "Supported formats: JPG, JPEG, or PNG."
        ),
        "ru": (
            "Отправьте чёткую портретную фотографию формата 3×4. "
            "Фотография для объективки обязательна.\n"
            "Поддерживаемые форматы: JPG, JPEG или PNG."
        ),
    },
    "send_cv_photo": {
        "uz": (
            "CV uchun yuzingiz aniq ko‘rinadigan professional rasm yuboring. "
            "Rasm qo‘shish ixtiyoriy — xohlamasangiz «Rasmsiz davom etish»ni bosing. "
            "Qo‘llab-quvvatlanadigan formatlar: JPG, JPEG yoki PNG."
        ),
        "en": (
            "Send a clear professional portrait for your resume. "
            "The photo is optional; choose Continue without photo to skip it. "
            "Supported formats: JPG, JPEG, or PNG."
        ),
        "ru": (
            "Отправьте чёткую профессиональную фотографию для резюме. "
            "Фото необязательно — можно продолжить без него. "
            "Поддерживаемые форматы: JPG, JPEG или PNG."
        ),
    },
    "photo_saved": {
        "uz": "✅ Rasm saqlandi.",
        "en": "✅ Photo saved.",
        "ru": "✅ Фотография сохранена.",
    },
    "photo_required": {
        "uz": "Avval JPG, JPEG yoki PNG formatidagi rasmni yuboring.",
        "en": "Please send a JPG, JPEG, or PNG image first.",
        "ru": "Сначала отправьте изображение в формате JPG, JPEG или PNG.",
    },
    "invalid_photo_format": {
        "uz": "Bu format mos emas. Rasmni JPG, JPEG yoki PNG formatida yuboring.",
        "en": "This format is not supported. Send a JPG, JPEG, or PNG image.",
        "ru": "Этот формат не поддерживается. Отправьте JPG, JPEG или PNG.",
    },
    "invalid_relative_birth": {
        "uz": "Tug‘ilgan sana va joyni quyidagi formatda kiriting: 20.03.1965, Toshkent shahri",
        "en": "Enter the birth date and place in this format: 20.03.1965, Tashkent",
        "ru": "Введите дату и место рождения в формате: 20.03.1965, Ташкент",
    },
    "stopped": {
        "uz": "⏹ Joriy hujjat yaratish to‘xtatildi.",
        "en": "⏹ Current document creation stopped.",
        "ru": "⏹ Создание текущего документа остановлено.",
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
    "education_saved": {
        "uz": "✅ Ta’lim ma’lumoti to‘liq saqlandi. Yana ta’lim qo‘shasizmi?",
        "en": "✅ The education entry is complete. Add another education entry?",
        "ru": "✅ Запись об образовании сохранена полностью. Добавить ещё одну?",
    },
    "choose_relatives": {
        "uz": (
            "Sizda qaysi yaqin qarindoshlar bor? Keraklilarini belgilang, "
            "so‘ng «Davom etish»ni bosing:"
        ),
        "en": "Which close relatives do you have? Select all that apply, then press Continue:",
        "ru": "Какие близкие родственники у вас есть? Выберите нужные и нажмите «Продолжить»:",
    },
    "choose_education_button": {
        "uz": "Ma’lumotingizni quyidagi tugmalardan birini bosib tanlang:",
        "en": "Choose your education level using one of the buttons below:",
        "ru": "Выберите уровень образования одной из кнопок:",
    },
    "choose_at_least_one_relative": {
        "uz": "Kamida bitta qarindosh turini belgilang yoki «Yo‘q»ni tanlang.",
        "en": "Select at least one relative type or choose None.",
        "ru": "Выберите хотя бы один тип родственника или вариант «Нет».",
    },
    "relative_saved_more": {
        "uz": "✅ Saqlandi. Shu qarindoshlikdan yana bormi?",
        "en": "✅ Saved. Do you have another relative of this type?",
        "ru": "✅ Сохранено. Есть ещё родственник этого типа?",
    },
    "old_button": {
        "uz": "Bu tugma eski savolga tegishli. Eng oxirgi xabardagi tugmalardan foydalaning.",
        "en": "This button belongs to an older question. Use the buttons in the latest message.",
        "ru": (
            "Эта кнопка относится к предыдущему вопросу. Используйте кнопки в последнем сообщении."
        ),
    },
    "help": {
        "uz": (
            "<b>Buyruqlar</b>\n/start — asosiy menyu\n/new — yangi hujjat\n"
            "/stop — joriy jarayonni to‘xtatish\n/my_cv — oxirgi hujjat\n"
            "/delete_me — barcha ma’lumotlarni o‘chirish"
        ),
        "en": (
            "<b>Commands</b>\n/start — main menu\n/new — new document\n"
            "/stop — stop current process\n/my_cv — latest document\n"
            "/delete_me — delete all my data"
        ),
        "ru": (
            "<b>Команды</b>\n/start — главное меню\n/new — новый документ\n"
            "/stop — остановить текущий процесс\n/my_cv — последний документ\n"
            "/delete_me — удалить все мои данные"
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
        "uz": "Ovozli javob uchun GEMINI_API_KEY sozlanmagan. Javobni matnda yuboring.",
        "en": "GEMINI_API_KEY is not configured for voice answers. Send the answer as text.",
        "ru": "Для голосовых ответов не настроен GEMINI_API_KEY. Отправьте ответ текстом.",
    },
    "voice_processing": {
        "uz": "🎙 Ovozli javob tushunilmoqda...",
        "en": "🎙 Understanding your voice answer...",
        "ru": "🎙 Распознаю голосовой ответ...",
    },
    "voice_transcribed": {
        "uz": "📝 Tushunilgan javob: <i>{answer}</i>",
        "en": "📝 Understood answer: <i>{answer}</i>",
        "ru": "📝 Распознанный ответ: <i>{answer}</i>",
    },
    "voice_too_large": {
        "uz": "Audio fayl juda katta. 20 MB dan kichikroq audio yuboring.",
        "en": "The audio file is too large. Send an audio file smaller than 20 MB.",
        "ru": "Аудиофайл слишком большой. Отправьте файл размером менее 20 МБ.",
    },
    "voice_error": {
        "uz": "Ovozli javobni tushunib bo‘lmadi. Qayta yuboring yoki matnda yozing.",
        "en": "The voice answer could not be understood. Try again or send it as text.",
        "ru": "Не удалось распознать голосовой ответ. Повторите или отправьте его текстом.",
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
        "uz": "Yashash joyingizni kiriting:",
        "en": "Enter your location:",
        "ru": "Укажите место проживания:",
    },
    "summary": {
        "uz": "O‘zingiz haqingizda qisqa professional ma’lumot yozing:",
        "en": "Write a short professional summary:",
        "ru": "Напишите краткое профессиональное описание:",
    },
    "skills": {
        "uz": "Ko‘nikmalaringizni vergul bilan ajratib kiriting (masalan: Java, SQL, Git):",
        "en": "Enter your skills separated by commas (for example: Java, SQL, Git):",
        "ru": "Введите навыки через запятую (например: Java, SQL, Git):",
    },
    "skill_suggestions_hint": {
        "uz": "Lavozimingizga mos ko‘nikmalar:",
        "en": "Skills suggested for your position:",
        "ru": "Навыки, рекомендованные для вашей должности:",
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
        "uz": "Bitta til va darajasini kiriting:",
        "en": "Enter one language and proficiency level:",
        "ru": "Введите один язык и уровень владения:",
    },
    "objective_full_name": {
        "uz": (
            "Ma’lumotnoma tepasiga chiqariladigan F.I.Sh.ni familiya, ism, "
            "otasining ismi tartibida kiriting:"
        ),
        "en": "Enter the full name for the heading: surname, first name, patronymic:",
        "ru": "Введите Ф.И.О. для заголовка: фамилия, имя, отчество:",
    },
    "objective_position": {
        "uz": "Hozirgi lavozimingizni kiriting (ish joyi nomini yozmang):",
        "en": "Enter your current position only (do not include the workplace):",
        "ru": "Укажите только текущую должность (без места работы):",
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
        "uz": "Ma’lumotingizni tanlang:",
        "en": "Choose your education level:",
        "ru": "Выберите уровень образования:",
    },
    "objective_graduated": {
        "uz": ("Shu bosqichdagi ta’lim muassasasi va o‘qigan yillaringizni kiriting:"),
        "en": ("Enter the institution and study years for this stage:"),
        "ru": ("Укажите учебное заведение и годы обучения на этой ступени:"),
    },
    "objective_specialty": {
        "uz": "Shu ta’lim bo‘yicha mutaxassisligingizni kiriting:",
        "en": "Enter the specialization for this education:",
        "ru": "Укажите специальность для этого образования:",
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
        "uz": "Bitta chet tili va bilish darajangizni kiriting:",
        "en": "Enter one foreign language and proficiency level:",
        "ru": "Введите один иностранный язык и уровень владения:",
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
        "uz": (
            "Mehnat faoliyatingizdagi bitta davrni kiriting. Ishlamagan bo‘lsangiz '-' yuboring "
            "(masalan: 2021–2025 — Toshkent davlat iqtisodiyot universiteti talabasi):"
        ),
        "en": (
            "Enter one period from your employment history. Send '-' if you have none "
            "(example: 2021–2025 — TSUE student):"
        ),
        "ru": (
            "Укажите один период трудовой деятельности. Если не работали, отправьте '-' "
            "(пример: 2021–2025 — студент ТГЭУ):"
        ),
    },
    "objective_relatives": {
        "uz": "Sizda bor yaqin qarindoshlarni tugmalar orqali belgilang:",
        "en": "Select the close relatives you have using the buttons:",
        "ru": "Выберите имеющихся близких родственников кнопками:",
    },
    "objective_relative_name": {
        "uz": "{relationship}ning familiyasi, ismi va otasining ismini kiriting:",
        "en": "Enter your {relationship}'s full name:",
        "ru": "Введите Ф.И.О. ({relationship}):",
    },
    "objective_relative_birth": {
        "uz": "{relationship}ning tug‘ilgan sanasi va joyini kiriting:",
        "en": "Enter your {relationship}'s date and place of birth:",
        "ru": "Введите дату и место рождения ({relationship}):",
    },
    "objective_relative_work": {
        "uz": "{relationship}ning ish joyi va lavozimini kiriting:",
        "en": "Enter your {relationship}'s workplace and position:",
        "ru": "Введите место работы и должность ({relationship}):",
    },
    "objective_relative_address": {
        "uz": "{relationship}ning yashash manzilini kiriting:",
        "en": "Enter your {relationship}'s home address:",
        "ru": "Введите адрес проживания ({relationship}):",
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
        "profile": "O‘ZIM HAQIMDA",
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
        "relative_birth": "Tug‘ilgan sanasi va joyi",
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
        "relative_birth": "Date and place of birth",
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
        "relative_birth": "Дата и место рождения",
        "relative_work": "Место работы и должность",
        "relative_address": "Адрес",
    },
}
