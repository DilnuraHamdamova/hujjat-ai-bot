# HujjatAI Telegram Bot

Foydalanuvchidan ma’lumot yig‘ib, PDF yoki DOCX formatida professional CV va
obyektivka yaratadigan uch tilli Telegram bot. Savollarga matn yoki ovoz/audio
orqali javob berish mumkin; audio javoblarni Gemini matnga aylantiradi.

## Hozir ishlaydigan imkoniyatlar

- Telegram polling (local/dev) va webhook (PROD)
- O‘zbek, ingliz va rus tillari
- Matn, Telegram voice va audio fayl orqali savollarga javob berish
- CV, obyektivka, tavsiyanoma va portfolio tanlov menyusi
- Classic, Modern va Europass uslubidagi CV shablonlari
- Majburiy 3×4 rasm va qarindoshlar jadvali bilan obyektivka
- Takrorlanuvchi ma’lumotlar uchun “Yana qo‘shish” oqimi
- Istalgan bo‘limni qo‘shish va keraksiz bo‘limni olib tashlash
- Telefon va email validatsiyasi
- PostgreSQL’da foydalanuvchi va versionlangan hujjat drafti
- Preview, maydonlarni tahrirlash va tasdiqlash
- PDF yoki Word formatidan faqat bittasini tanlash
- Bitta canonical JSON’dan hujjat yaratish
- Redis + Celery background-worker infratuzilmasi
- Webhook secret va takroriy update himoyasi
- `/delete_me` orqali DB va yaratilgan hujjatlarni o‘chirish
- Docker Compose, healthcheck va Alembic migration

Tavsiyanoma tugmasi hozircha “tez orada” holatida. Portfolio oqimi esa bot ichida
ma’lumotlarni yig‘adi, self-contained HTML yaratadi va foydalanuvchining Netlify Personal
Access Token’i bilan yangi saytga deploy qilib, live URL’ni qaytaradi. Token saqlanmaydi.

## Arxitektura

```text
Telegram
   │
   ▼
FastAPI + aiogram ─── PostgreSQL
   │
   ├── Jinja2 + WeasyPrint ── CV/obyektivka PDF
   ├── python-docx ────────── CV/obyektivka DOCX
   ├── Gemini ─────────────── voice/audio transkripsiya
   └── Redis + Celery ─────── background tasklar
```

## Hozir qaysi API key kerak?

`BOT_TOKEN` botni ishlatish uchun, `GEMINI_API_KEY` esa voice/audio javoblar uchun kerak. Telegram tokenini `@BotFather` orqali oling:

1. `@BotFather`ni oching.
2. `/newbot` yuboring.
3. Bot nomi va `...bot` bilan tugaydigan username kiriting.
4. Berilgan tokenni nusxalang.
5. Tokenni hech kimga yubormang va Git’ga commit qilmang.

`GEMINI_API_KEY` bo‘sh qolsa, text funksiyalar ishlaydi, faqat voice/audio transkripsiya o‘chiriladi.

## Docker bilan ishga tushirish

```bash
cd /home/vivobook/IdeaProjects/cv-telegram-bot
cp .env.example .env
```

`.env` ichida faqat quyidagini haqiqiy token bilan almashtiring:

```env
BOT_TOKEN=BotFather-bergan-token
BOT_MODE=polling
GEMINI_API_KEY=Google-AI-Studio-bergan-kalit
GEMINI_MODEL=gemini-3.6-flash
GEMINI_ROUTER_MODEL=gemini-3.5-flash-lite
GEMINI_VOICE_MODEL=gemini-3.5-transcribe
```

Keyin:

```bash
docker compose up --build -d
docker compose logs -f app
```

Telegram’da botni ochib `/start` yuboring. Local polling rejimida domen yoki HTTPS
kerak emas.

To‘xtatish:

```bash
docker compose down
```

Volume’dagi database ma’lumotlari saqlanib qoladi. Ularni o‘chirish uchun `down -v`
ishlatmang, agar barcha ma’lumotni ataylab yo‘qotmoqchi bo‘lmasangiz.

## IntelliJ IDEA’da ochish

`File → Open` orqali quyidagi papkani tanlang:

```text
/home/vivobook/IdeaProjects/cv-telegram-bot
```

Python SDK sifatida loyiha ichidagi `.venv/bin/python`ni tanlash mumkin.

## Local Python development

PostgreSQL va Redis’ni Docker’da, app’ni host’da ishlatmoqchi bo‘lsangiz `.env`dagi
hostlarni `localhost`ga almashtiring.

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q
.venv/bin/ruff check .
```

## PROD webhook

Production serverda HTTPS domen tayyor bo‘lgach:

```env
APP_ENV=production
BOT_MODE=webhook
WEBHOOK_BASE_URL=https://bot.example.uz
WEBHOOK_PATH=/telegram/webhook
WEBHOOK_SECRET=uzun-tasodifiy-secret
```

Reverse proxy faqat `8000` portdagi app’ga trafik uzatadi. Telegram tokeni, webhook
secret va database internetga ochilmaydi.

## Gemini integratsiyasi

`app/services/ai.py` ichidagi `GeminiProvider`:

- Telegram voice va audio faylni past kechikish uchun maxsus
  `gemini-3.5-transcribe` modeli orqali matnga aylantiradi;
- joriy savol va foydalanuvchi tilini transkripsiya konteksti sifatida uzatadi;
- tushunilgan matnni oddiy text javob bilan bir xil validatsiya va saqlash oqimiga beradi;
- `extract_resume()` orqali erkin matndan strukturali CV ma’lumotini ajrata oladi;
- API kalit bo‘lmasa text-only fallbackni saqlaydi.

Audio hajmi 20 MB bilan cheklangan. Vaqtinchalik audio fayllar transkripsiyadan
keyin avtomatik o‘chiriladi.
