"""Generate a static portfolio and publish it to Netlify."""

# The generated inline HTML intentionally keeps the template compact.
# ruff: noqa: E501

from __future__ import annotations

import io
import re
import zipfile
from html import escape

import httpx


class PortfolioDeploymentError(RuntimeError):
    pass


_URL_PATTERN = re.compile(r"https?://[^\s<>\"]+")


def render_portfolio(data: dict[str, object]) -> str:
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

    def section(title: str, body: str, section_id: str = "") -> str:
        if not body:
            return ""
        anchor = ' id="' + escape(section_id) + '"' if section_id else ""
        return (
            "<section"
            + anchor
            + '><p class="eyebrow">'
            + escape(title)
            + "</p>"
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
    sections = [
        section("About", '<p class="statement">' + summary_html + "</p>", "about")
        if summary_html
        else "",
        section("Skills", '<ul class="skills">' + skills_html + "</ul>", "skills")
        if skills_html
        else "",
        section("Experience", '<div class="grid">' + experience_html + "</div>", "experience")
        if experience_html
        else "",
        section("Education", '<div class="grid">' + education_html + "</div>", "education")
        if education_html
        else "",
        section("Languages", '<div class="grid">' + languages_html + "</div>", "languages")
        if languages_html
        else "",
    ]
    custom_sections = data.get("portfolio_sections", [])
    if isinstance(custom_sections, list):
        for item in custom_sections:
            if not isinstance(item, dict) or not item.get("content"):
                continue
            key = str(item.get("key", ""))
            title = str(item.get("title", key.replace("_", " ").title()))
            body = '<article class="card wide"><p>' + rich(item.get("content")) + "</p></article>"
            sections.append(section(title, body, key))
    themes = {
        "minimal": ("#111827", "#ffffff", "#f3f4f6", "#4b5563"),
        "modern": ("#6d5dfc", "#f7f8fc", "#ffffff", "#667085"),
        "creative": ("#ec4899", "#fff7ed", "#ffffff", "#6b5470"),
        "developer": ("#a3ff5f", "#07130b", "#102117", "#b8c9bd"),
    }
    accent, background, surface, muted = themes.get(
        str(data.get("portfolio_template")), themes["modern"]
    )
    contact_items = " · ".join(
        value for value in (esc("email"), esc("phone"), esc("location")) if value
    )
    sections_html = "".join(sections)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{esc("full_name")} — {esc("job_title")} portfolio"><title>{esc("full_name")} — Portfolio</title>
<style>:root{{--accent:{accent};--bg:{background};--surface:{surface};--muted:{muted}}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--muted);font-family:Inter,ui-sans-serif,system-ui,sans-serif;line-height:1.7}}a{{color:var(--accent)}}header,main,footer{{width:min(1080px,calc(100% - 40px));margin:auto}}header{{display:flex;justify-content:space-between;align-items:center;padding:28px 0;border-bottom:1px solid color-mix(in srgb,var(--muted) 22%,transparent)}}nav{{display:flex;gap:24px}}nav a{{color:var(--muted);text-decoration:none}}.hero{{min-height:72vh;display:grid;align-content:center;padding:80px 0}}h1{{max-width:900px;margin:12px 0;font-size:clamp(3.6rem,11vw,8rem);letter-spacing:-.075em;line-height:.88;color:var(--accent)}}.role,.statement{{font-size:clamp(1.2rem,2.6vw,2rem);max-width:780px}}.eyebrow{{font:700 .75rem ui-monospace,monospace;letter-spacing:.18em;text-transform:uppercase;color:var(--accent)}}section{{padding:78px 0;border-top:1px solid color-mix(in srgb,var(--muted) 22%,transparent)}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}}.card{{padding:28px;border:1px solid color-mix(in srgb,var(--muted) 20%,transparent);border-radius:22px;background:var(--surface)}}.card p{{margin:0}}.wide{{max-width:900px}}.skills{{display:flex;flex-wrap:wrap;gap:10px;padding:0;list-style:none}}.skills li{{padding:10px 16px;border-radius:999px;background:var(--surface);border:1px solid color-mix(in srgb,var(--muted) 18%,transparent)}}.contact{{font-size:clamp(1rem,2.4vw,1.6rem)}}footer{{padding:35px 0 55px;border-top:1px solid color-mix(in srgb,var(--muted) 22%,transparent)}}@media(max-width:680px){{nav{{display:none}}.hero{{min-height:62vh}}.grid{{grid-template-columns:1fr}}section{{padding:52px 0}}}}</style></head>
<body><header><strong>{esc("full_name", "Portfolio")}</strong><nav><a href="#about">About</a><a href="#experience">Experience</a><a href="#contact">Contact</a></nav></header><main><div class="hero"><p class="eyebrow">{esc("location", "Portfolio")}</p><h1>{esc("full_name", "Your name")}</h1><p class="role">{esc("job_title")}</p><p>{esc("portfolio_tagline")}</p></div>{sections_html}<section id="contact"><p class="eyebrow">Contact</p><p class="contact">{contact_items}</p></section></main><footer>Built with care · {esc("full_name", "Portfolio")}</footer></body></html>"""


def portfolio_zip(document: str) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("index.html", document)
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
            deploy_response = await client.post(
                f"https://api.netlify.com/api/v1/sites/{site['id']}/deploys",
                headers={**headers, "Content-Type": "application/zip"},
                content=portfolio_zip(document),
            )
            if deploy_response.is_error:
                raise PortfolioDeploymentError("Netlify deploy xatosi yuz berdi.")
            deploy = deploy_response.json()
            url = (
                deploy.get("ssl_url")
                or deploy.get("deploy_ssl_url")
                or site.get("ssl_url")
                or site.get("url")
            )
            if not url:
                raise PortfolioDeploymentError("Netlify javobida sayt manzili topilmadi.")
            return str(url)
    except httpx.HTTPError as error:
        raise PortfolioDeploymentError("Netlify bilan bog‘lanib bo‘lmadi.") from error
