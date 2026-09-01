# HujjatAI Telegram Bot

Foydalanuvchidan ma’lumot yig‘ib, PDF yoki DOCX formatida professional CV va
obyektivka yaratadigan uch tilli Telegram bot. OpenAI integratsiyasi keyingi bosqich
uchun ajratilgan; hozirgi versiya OpenAI API key’siz ishlaydi.

## Hozir ishlaydigan imkoniyatlar

- Telegram polling (local/dev) va webhook (PROD)
- O‘zbek, ingliz va rus tillari
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

Tavsiyanoma va portfolio tugmalari menyuda mavjud, lekin hozircha “tez orada”
holatida. Tavsiyanoma AI orqali, portfolio esa keyingi Netlify integratsiyasi orqali
ishlaydi.

## Arxitektura

```text
Telegram
   │
   ▼
FastAPI + aiogram ─── PostgreSQL
   │
   ├── Jinja2 + WeasyPrint ── CV/obyektivka PDF
   ├── python-docx ────────── CV/obyektivka DOCX
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

`app/services/ai.py` ichidagi `AIProvider` contract o‘zgarmaydi. Keyingi bosqichda
`OpenAIProvider` qo‘shilib:

- `transcribe()` — Telegram voice’ni matnga aylantiradi;
- `extract_resume()` — bitta erkin matndan strukturali ma’lumot oladi;
- yetishmagan majburiy maydonlarni aniqlab, foydalanuvchidan so‘raydi;
- foydalanuvchi mazmunidan tavsiyanoma yaratadi.

Bot handlerlari va hujjat generatorini qayta yozish talab qilinmaydi.
