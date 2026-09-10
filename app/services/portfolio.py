"""Generate a static portfolio and publish it to Netlify."""

# The generated inline HTML intentionally keeps the template compact.
# ruff: noqa: E501

from __future__ import annotations

import base64
import asyncio
import io
import mimetypes
import re
import zipfile
from html import escape

import httpx

from app.services.localization import PORTFOLIO_SECTION_LABELS, Language, normalize_language


class PortfolioDeploymentError(RuntimeError):
    pass


_URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")


_PAGE_COPY: dict[Language, dict[str, str]] = {
    "uz": {
        "portfolio": "Portfolio",
        "available": "Yangi loyihalar uchun ochiq",
        "explore": "Ishlarimni ko‘rish",
        "contact_cta": "Bog‘lanish",
        "featured": "Tanlangan ma’lumotlar",
        "contact_intro": "Birgalikda ajoyib mahsulot yaratamiz.",
        "footer": "E’tibor va mahorat bilan yaratildi",
        "top": "Yuqoriga",
    },
    "en": {
        "portfolio": "Portfolio",
        "available": "Available for select projects",
        "explore": "Explore my work",
        "contact_cta": "Get in touch",
        "featured": "Selected profile",
        "contact_intro": "Let’s create something remarkable together.",
        "footer": "Built with care and craft",
        "top": "Back to top",
    },
    "ru": {
        "portfolio": "Портфолио",
        "available": "Открыт(а) для новых проектов",
        "explore": "Смотреть мои работы",
        "contact_cta": "Связаться",
        "featured": "Избранная информация",
        "contact_intro": "Давайте вместе создадим нечто выдающееся.",
        "footer": "Создано с вниманием к деталям",
        "top": "Наверх",
    },
}


def render_portfolio(data: dict[str, object], language: str = "uz") -> str:
    locale = normalize_language(language)
    copy = _PAGE_COPY[locale]
    labels = PORTFOLIO_SECTION_LABELS[locale]

    def esc(key: str, default: str = "") -> str:
        return escape(str(data.get(key, default) or "").strip())

    def rich(value: object) -> str:
        raw = str(value or "").strip()
        output: list[str] = []
        cursor = 0
        for match in _URL_PATTERN.finditer(raw):
            output.append(escape(raw[cursor : match.start()]))
            url = match.group(0).rstrip(".,;:!?)")
            suffix = match.group(0)[len(url) :]
            safe_url = escape(url, quote=True)
            output.append(
                f'<a href="{safe_url}" target="_blank" rel="noreferrer">'
                f"{escape(url)}</a>{escape(suffix)}"
            )
            cursor = match.end()
        output.append(escape(raw[cursor:]))
        return "".join(output).replace("\n", "<br>")

    def cards_for(key: str) -> str:
        values = data.get(key, [])
        if not isinstance(values, list):
            return ""
        return "".join(
            '<article class="card"><p>' + rich(item) + "</p></article>"
            for item in values
            if str(item).strip()
        )

    def project_cards() -> str:
        values = data.get("projects", [])
        if not isinstance(values, list):
            return ""
        cards: list[str] = []
        for item in values:
            lines = [line.strip(" •-\t") for line in str(item).splitlines() if line.strip()]
            if not lines:
                continue
            title, *details = lines
            detail_html = "".join(f"<li>{rich(line)}</li>" for line in details)
            if not detail_html:
                detail_html = f"<li>{rich(title)}</li>"
                title = "Loyiha"
            cards.append(
                '<article class="card project-card"><h3>'
                + rich(title)
                + '</h3><ul class="project-points">'
                + detail_html
                + "</ul></article>"
            )
        return "".join(cards)

    def section(title: str, body: str, section_id: str = "") -> str:
        if not body:
            return ""
        anchor = ' id="' + escape(section_id) + '"' if section_id else ""
        return (
            "<section"
            + anchor
            + ' class="content-section"><div class="section-heading"><p class="eyebrow">'
            + escape(title)
            + "</p><span>↘</span></div>"
            + body
            + "</section>"
        )

    skills = data.get("skills", [])
    skills_html = (
        "".join("<li>" + escape(str(item)) + "</li>" for item in skills if str(item).strip())
        if isinstance(skills, list)
        else ""
    )
    summary_html = esc("summary")
    experience_html = cards_for("experience")
    education_html = cards_for("education")
    languages_html = cards_for("languages")
    projects_html = project_cards()
    sections = [
        section(labels["about"], '<p class="statement">' + summary_html + "</p>", "about")
        if summary_html
        else "",
        section(labels["skills"], '<ul class="skills">' + skills_html + "</ul>", "skills")
        if skills_html
        else "",
        section(
            labels["experience"],
            '<div class="grid">' + experience_html + "</div>",
            "experience",
        )
        if experience_html
        else "",
        section(
            labels["education"],
            '<div class="grid">' + education_html + "</div>",
            "education",
        )
        if education_html
        else "",
        section(
            labels["languages"],
            '<div class="grid">' + languages_html + "</div>",
            "languages",
        )
        if languages_html
        else "",
        section(labels["projects"], '<div class="project-list">' + projects_html + "</div>", "projects")
        if projects_html
        else "",
    ]
    custom_sections = data.get("portfolio_sections", [])
    if isinstance(custom_sections, list):
        for item in custom_sections:
            if not isinstance(item, dict) or not item.get("content"):
                continue
            key = str(item.get("key", ""))
            title = labels.get(key, str(item.get("title", key.replace("_", " ").title())))
            body = '<article class="card wide"><p>' + rich(item.get("content")) + "</p></article>"
            sections.append(section(title, body, key))
    themes = {
        "minimal": ("#151515", "#d8ff63", "#f2efe7", "#ffffff", "#151515", "#67665f"),
        "modern": ("#765cff", "#b9ff66", "#090817", "#141226", "#f5f3ff", "#aaa5bf"),
        "creative": ("#ff5f9e", "#ffdf65", "#130913", "#281225", "#fff4fb", "#cbb0c6"),
        "developer": ("#b8ff5a", "#6d7cff", "#07100a", "#101d14", "#eff8f0", "#a4b3a7"),
    }
    accent, accent_two, background, surface, foreground, muted = themes.get(
        str(data.get("portfolio_template")), themes["modern"]
    )
    section_ids = re.findall(r'id="([^"]+)"', "".join(sections))
    nav_items = "".join(
        f'<a href="#{escape(section_id)}">{escape(labels.get(section_id, section_id.title()))}</a>'
        for section_id in section_ids[:4]
    )
    sections_html = "".join(sections)
    photo_html = ""
    photo_path = str(data.get("photo_path", "") or "")
    if photo_path:
        try:
            mime = mimetypes.guess_type(photo_path)[0] or "image/jpeg"
            encoded = base64.b64encode(open(photo_path, "rb").read()).decode("ascii")
            photo_html = f'<img class="profile-photo" style="position:absolute;inset:50px;width:calc(100% - 100px);height:calc(100% - 100px);object-fit:cover;border-radius:24px;opacity:.72" src="data:{mime};base64,{encoded}" alt="{esc("full_name", copy["portfolio"])}">'
        except (OSError, ValueError):
            photo_html = ""
    email = esc("email")
    phone = esc("phone")
    location = esc("location")
    contact_items = "".join(
        item
        for item in (
            f'<a href="mailto:{email}">{email}<span>↗</span></a>' if email else "",
            f'<a href="tel:{phone}">{phone}<span>↗</span></a>' if phone else "",
            f"<p>{location}</p>" if location else "",
        )
    )
    return f"""<!doctype html><html lang="{locale}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{esc("full_name")} — {esc("job_title")} {escape(copy["portfolio"].lower())}"><meta name="theme-color" content="{background}"><title>{esc("full_name")} — {escape(copy["portfolio"])}</title>
<style>
:root{{--accent:{accent};--accent-2:{accent_two};--bg:{background};--surface:{surface};--fg:{foreground};--muted:{muted};--line:color-mix(in srgb,var(--muted) 20%,transparent)}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;overflow-x:hidden;background:var(--bg);color:var(--muted);font-family:Inter,"SF Pro Display",ui-sans-serif,system-ui,sans-serif;line-height:1.7}}body:before,body:after{{content:"";position:fixed;z-index:-2;width:44rem;height:44rem;border-radius:50%;filter:blur(110px);opacity:.2;pointer-events:none}}body:before{{top:-18rem;right:-12rem;background:var(--accent)}}body:after{{bottom:-24rem;left:-16rem;background:var(--accent-2)}}.backdrop{{position:fixed;inset:0;z-index:-1;opacity:.35;background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);background-size:72px 72px;mask-image:linear-gradient(to bottom,black,transparent 82%);pointer-events:none}}a{{color:inherit}}header,main,footer{{width:min(1180px,calc(100% - 40px));margin:auto}}header{{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center;gap:30px;padding:22px 0;border-bottom:1px solid var(--line);background:color-mix(in srgb,var(--bg) 84%,transparent);backdrop-filter:blur(18px)}}.brand{{color:var(--fg);font-size:1rem;font-weight:800;letter-spacing:-.03em;text-decoration:none}}.brand i{{color:var(--accent);font-style:normal}}nav{{display:flex;gap:22px}}nav a{{font-size:.72rem;text-decoration:none;transition:color .2s}}nav a:hover{{color:var(--fg)}}.status{{display:flex;align-items:center;gap:9px;font:600 .65rem ui-monospace,monospace;text-transform:uppercase;letter-spacing:.08em}}.status:before{{content:"";width:8px;height:8px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 6px color-mix(in srgb,var(--accent) 12%,transparent)}}.hero{{min-height:82vh;display:grid;grid-template-columns:1.15fr .85fr;gap:clamp(40px,7vw,100px);align-items:center;padding:100px 0}}.eyebrow{{margin:0;color:var(--accent);font:700 .68rem ui-monospace,monospace;letter-spacing:.18em;text-transform:uppercase}}h1{{max-width:850px;margin:24px 0 20px;color:var(--fg);font-size:clamp(4rem,10vw,8.8rem);font-weight:700;letter-spacing:-.085em;line-height:.82}}.role{{margin:0;color:var(--fg);font-size:clamp(1.25rem,2.6vw,2rem);font-weight:550;letter-spacing:-.035em}}.tagline{{max-width:660px;margin:18px 0 0;font-size:1.05rem}}.actions{{display:flex;flex-wrap:wrap;gap:13px;margin-top:36px}}.button{{padding:13px 18px;border:1px solid var(--line);border-radius:999px;font:700 .68rem ui-monospace,monospace;text-decoration:none;text-transform:uppercase;letter-spacing:.08em;transition:.2s}}.button.primary{{border-color:var(--accent);color:var(--bg);background:var(--accent)}}.button:hover{{transform:translateY(-3px);box-shadow:0 14px 36px color-mix(in srgb,var(--accent) 18%,transparent)}}.hero-art{{position:relative;min-height:480px;border:1px solid var(--line);border-radius:36px;background:linear-gradient(145deg,color-mix(in srgb,var(--surface) 92%,var(--accent) 8%),var(--surface));box-shadow:0 35px 100px rgba(0,0,0,.24);overflow:hidden}}.hero-art:before{{content:"";position:absolute;width:340px;height:340px;right:-80px;top:-80px;border-radius:50%;background:radial-gradient(circle at 35% 35%,white,var(--accent) 14%,transparent 68%);opacity:.8}}.hero-art:after{{content:"</>";position:absolute;right:35px;bottom:12px;color:color-mix(in srgb,var(--fg) 8%,transparent);font:800 9rem ui-monospace,monospace;letter-spacing:-.15em}}.signal{{position:absolute;inset:50px;display:flex;flex-direction:column;justify-content:flex-end;padding:32px;border-radius:24px;border:1px solid var(--line);background:color-mix(in srgb,var(--bg) 66%,transparent);backdrop-filter:blur(14px)}}.signal b{{position:relative;z-index:1;color:var(--fg);font-size:clamp(2rem,4vw,3.9rem);line-height:1;letter-spacing:-.07em}}.signal span{{position:relative;z-index:1;margin-top:14px;color:var(--accent);font:700 .66rem ui-monospace,monospace;text-transform:uppercase;letter-spacing:.12em}}.content-section{{padding:90px 0;border-top:1px solid var(--line)}}.section-heading{{display:flex;align-items:center;justify-content:space-between;margin-bottom:42px}}.section-heading span{{color:var(--accent);font-size:1.6rem}}.statement{{max-width:980px;margin:0;color:var(--fg);font-size:clamp(1.55rem,4vw,3.4rem);font-weight:560;letter-spacing:-.05em;line-height:1.18}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}.card{{position:relative;padding:30px;border:1px solid var(--line);border-radius:24px;background:color-mix(in srgb,var(--surface) 90%,transparent);overflow:hidden;transition:.25s}}.card:before{{content:"";position:absolute;left:0;top:0;width:3px;height:100%;background:linear-gradient(var(--accent),var(--accent-2));opacity:.75}}.card:hover{{border-color:color-mix(in srgb,var(--accent) 45%,transparent);transform:translateY(-4px)}}.card p{{position:relative;margin:0;white-space:normal}}.card a{{color:var(--accent);text-underline-offset:4px}}.wide{{max-width:none;min-height:160px;font-size:1.03rem}}.skills{{display:flex;flex-wrap:wrap;gap:10px;padding:0;list-style:none}}.skills li{{padding:11px 16px;border:1px solid var(--line);border-radius:999px;color:var(--fg);background:var(--surface);font:600 .75rem ui-monospace,monospace;transition:.2s}}.skills li:hover{{color:var(--bg);border-color:var(--accent);background:var(--accent);transform:translateY(-3px)}}.contact-block{{padding:110px 0;border-top:1px solid var(--line)}}.contact-block h2{{max-width:920px;margin:18px 0 54px;color:var(--fg);font-size:clamp(2.8rem,7vw,6.6rem);line-height:.95;letter-spacing:-.07em}}.contact-list{{display:grid;border-top:1px solid var(--line)}}.contact-list>a,.contact-list>p{{display:flex;justify-content:space-between;margin:0;padding:18px 0;border-bottom:1px solid var(--line);color:var(--fg);font-size:clamp(1rem,2vw,1.35rem);text-decoration:none}}.contact-list>a:hover{{color:var(--accent)}}footer{{display:flex;justify-content:space-between;gap:20px;padding:34px 0 48px;border-top:1px solid var(--line);font:600 .65rem ui-monospace,monospace;text-transform:uppercase;letter-spacing:.08em}}footer a{{text-decoration:none;color:var(--accent)}}@media(max-width:820px){{nav{{display:none}}.status{{font-size:0;gap:0}}.hero{{min-height:auto;grid-template-columns:1fr;padding:75px 0}}.hero-art{{min-height:380px}}.signal{{inset:28px}}.grid{{grid-template-columns:1fr}}.content-section{{padding:64px 0}}}}@media(max-width:520px){{header,main,footer{{width:min(100% - 28px,1180px)}}h1{{font-size:clamp(3.4rem,20vw,5rem)}}.hero-art{{min-height:330px;border-radius:25px}}.signal{{inset:18px;padding:22px}}.contact-block{{padding:75px 0}}footer{{flex-direction:column}}}}@media(prefers-reduced-motion:no-preference){{.hero-art{{animation:float 6s ease-in-out infinite}}@keyframes float{{50%{{transform:translateY(-10px)}}}}}}
</style></head><body><div class="backdrop" aria-hidden="true"></div><header><a class="brand" href="#top">{esc("full_name", copy["portfolio"])}<i>.</i></a><nav>{nav_items}<a href="#contact">{escape(labels["contact"])}</a></nav><div class="status">{escape(copy["available"])}</div></header><main id="top"><div class="hero"><div><p class="eyebrow">{escape(copy["featured"])}</p><h1>{esc("full_name", copy["portfolio"])}</h1><p class="role">{esc("job_title")}</p><p class="tagline">{esc("portfolio_tagline")}</p><div class="actions"><a class="button primary" href="#projects">{escape(copy["explore"])} ↗</a><a class="button" href="#contact">{escape(copy["contact_cta"])}</a></div></div><div class="hero-art">{photo_html}<div class="signal"><b>{esc("job_title", copy["portfolio"])}</b><span>{escape(copy["available"])}</span></div></div></div>{sections_html}<section class="contact-block" id="contact"><p class="eyebrow">{escape(labels["contact"])}</p><h2>{escape(copy["contact_intro"])}</h2><div class="contact-list">{contact_items}</div></section></main><footer><span>© {esc("full_name", copy["portfolio"])} · {escape(copy["footer"])}</span><a href="#top">{escape(copy["top"])} ↑</a></footer></body></html>"""


def portfolio_zip(document: str) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("index.html", document)
        # Explicitly set the response MIME type. This prevents accounts with
        # restrictive Netlify defaults from serving index.html as text/plain.
        archive.writestr("_headers", "/*\n  Content-Type: text/html; charset=UTF-8\n")
    return output.getvalue()


async def deploy_to_netlify(document: str, token: str, site_name: str) -> str:
    token = token.strip()
    if len(token) < 10:
        raise PortfolioDeploymentError("Netlify token juda qisqa yoki noto‘g‘ri.")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            site_response = await client.post(
                "https://api.netlify.com/api/v1/sites", headers=headers, json={"name": site_name}
            )
            if site_response.is_error:
                raise PortfolioDeploymentError(
                    "Netlify site yaratmadi. Token yoki sayt nomini tekshiring."
                )
            site = site_response.json()
            payload = portfolio_zip(document)
            deploy_response = await client.post(
                f"https://api.netlify.com/api/v1/sites/{site['id']}/deploys",
                headers={**headers, "Content-Type": "application/zip"},
                content=payload,
            )
            if deploy_response.is_error:
                raise PortfolioDeploymentError("Netlify deploy xatosi yuz berdi.")
            deploy = deploy_response.json()
            deploy_id = deploy.get("id")
            if not deploy_id:
                raise PortfolioDeploymentError("Netlify deploy ID qaytarmadi.")
            # ZIP deploys are asynchronous. Wait for the deploy itself to become
            # ready before probing the public URL; otherwise the old/placeholder
            # response can be mistaken for a broken HTML page.
            for _ in range(30):
                state_response = await client.get(
                    f"https://api.netlify.com/api/v1/sites/{site['id']}/deploys/{deploy_id}",
                    headers=headers,
                )
                if state_response.is_success:
                    state = str(state_response.json().get("state", ""))
                    if state in {"ready", "uploaded"}:
                        deploy = state_response.json()
                        break
                    if state in {"error", "failed"}:
                        raise PortfolioDeploymentError("Netlify deploy yakunlanmadi.")
                await asyncio.sleep(2)
            url = (
                # Deploy-preview URLs may be protected by Netlify team access
                # control. The site URL is the public, shareable address.
                site.get("ssl_url")
                or site.get("url")
                or deploy.get("ssl_url")
                or deploy.get("deploy_ssl_url")
            )
            if not url:
                raise PortfolioDeploymentError("Netlify javobida sayt manzili topilmadi.")
            # Do not return a broken link: wait for Netlify post-processing and
            # verify that the public endpoint serves HTML (not the source as text).
            public_url = str(url)
            for attempt in range(8):
                try:
                    page = await client.get(public_url, follow_redirects=True)
                    content_type = page.headers.get("content-type", "").lower()
                    body_start = page.text.lstrip().lower()[:128]
                    if page.is_success and "text/html" in content_type and (
                        "<!doctype html" in body_start or "<html" in body_start
                    ):
                        return public_url
                except httpx.HTTPError:
                    pass
                if attempt < 7:
                    await asyncio.sleep(2)
            raise PortfolioDeploymentError(
                "Netlify deploy yakunlandi, lekin sayt HTML sifatida ochilmadi. Qayta urinib ko‘ring."
            )
    except httpx.HTTPError as error:
        raise PortfolioDeploymentError("Netlify bilan bog‘lanib bo‘lmadi.") from error
