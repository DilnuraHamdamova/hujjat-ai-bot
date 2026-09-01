# CV Telegram Bot

Matn orqali foydalanuvchidan ma’lumot yig‘ib, ATS-friendly PDF va DOCX CV yaratadigan
Telegram bot. OpenAI integratsiyasi keyingi bosqich uchun ajratilgan, ammo hozirgi MVP
OpenAI API key’siz to‘liq ishlaydi.

## Hozir ishlaydigan imkoniyatlar

- Telegram polling (local/dev) va webhook (PROD)
- Ketma-ket matnli savol-javob
- Telefon va email validatsiyasi
- PostgreSQL’da user va versionlangan CV draft
- Preview, maydonlarni tahrirlash va tasdiqlash
- Bitta canonical JSON’dan PDF va DOCX
- Redis + Celery background-worker infratuzilmasi
- Webhook secret va takroriy update himoyasi
- `/delete_me` orqali DB va yaratilgan hujjatlarni o‘chirish
- Docker Compose, healthcheck va Alembic migration

## Arxitektura

```text
Telegram
   │
   ▼
FastAPI + aiogram ─── PostgreSQL
   │
   ├── Jinja2 + WeasyPrint ── PDF
   ├── python-docx ────────── DOCX
   └── Redis + Celery ─────── kelajakdagi audio/AI tasklar
```

## Hozir qaysi API key kerak?

Faqat `BOT_TOKEN` kerak. Uni Telegram’dagi `@BotFather` orqali oling:

1. `@BotFather`ni oching.
2. `/newbot` yuboring.
3. Bot nomi va `...bot` bilan tugaydigan username kiriting.
4. Berilgan tokenni nusxalang.
5. Tokenni hech kimga yubormang va Git’ga commit qilmang.

`OPENAI_API_KEY` hozir bo‘sh qoladi.

## Docker bilan ishga tushirish

```bash
cd /home/vivobook/IdeaProjects/cv-telegram-bot
cp .env.example .env
```

`.env` ichida faqat quyidagini haqiqiy token bilan almashtiring:

```env
BOT_TOKEN=BotFather-bergan-token
BOT_MODE=polling
OPENAI_API_KEY=
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

## OpenAI keyin qanday ulanadi?

`app/services/ai.py` ichidagi `AIProvider` contract o‘zgarmaydi. Keyinchalik
`OpenAIProvider` qo‘shilib:

- `transcribe()` — Telegram voice’ni matnga aylantiradi;
- `extract_resume()` — erkin matndan strukturali `ResumeData` oladi.

Bot handlerlari va hujjat generatorini qayta yozish talab qilinmaydi.
