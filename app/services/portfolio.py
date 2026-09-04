"""Generate a static portfolio and publish it to Netlify."""

# The generated inline HTML intentionally keeps the template compact.
# ruff: noqa: E501

from __future__ import annotations

import io
import zipfile
from html import escape

import httpx


class PortfolioDeploymentError(RuntimeError):
    pass


def render_portfolio(data: dict[str, object]) -> str:
    def esc(key: str, default: str = "") -> str:
        return escape(str(data.get(key, default) or "").strip())
    skills = data.get("skills", [])
    skills_html = "".join(f"<li>{escape(str(item))}</li>" for item in skills if str(item).strip()) if isinstance(skills, list) else ""
    projects = data.get("experience", [])
    custom_sections = data.get("portfolio_sections", [])
    custom_html = (
        "".join(
            f"<section><h2>{escape(str(item.get('title', '')))}</h2>"
            f"<p>{escape(str(item.get('content', '')))}</p></section>"
            for item in custom_sections
            if isinstance(item, dict) and item.get("content")
        )
        if isinstance(custom_sections, list)
        else ""
    )
    themes = {
        "minimal": ("#111827", "#374151", "#ffffff"),
        "modern": ("#6d5dfc", "#18202a", "#f7f8fc"),
        "creative": ("#ec4899", "#312e81", "#fff7ed"),
        "developer": ("#22c55e", "#d1fae5", "#07130b"),
    }
    accent, ink, background = themes.get(str(data.get("portfolio_template")), themes["modern"])
    cards = "".join(f"<article><h3>{escape(str(item))}</h3></article>" for item in projects if str(item).strip()) if isinstance(projects, list) else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc("full_name")} — Portfolio</title>
<style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:auto;padding:8vw 6vw;color:{ink};background:{background}}}h1{{font-size:clamp(3rem,10vw,6rem);line-height:1;margin:.2em 0}}h2{{margin-top:3rem;color:{accent}}}.lead{{font-size:1.5rem;color:#667085}}ul{{display:flex;flex-wrap:wrap;gap:10px;padding:0;list-style:none}}li,article{{background:white;border-radius:14px;padding:14px 18px;box-shadow:0 8px 24px #18202a12}}a{{color:{accent};font-weight:700}}</style></head>
<body><p>{esc("location", "Portfolio")}</p><h1>{esc("full_name")}</h1><p class="lead">{esc("job_title")}</p>
<section><h2>About me</h2><p>{esc("summary")}</p></section>
{f'<section><h2>Skills</h2><ul>{skills_html}</ul></section>' if skills_html else ''}
{f'<section><h2>Experience</h2>{cards}</section>' if cards else ''}
{custom_html}
<section><h2>Contact</h2><p>{esc("email")}</p></section></body></html>'''


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
                raise PortfolioDeploymentError("Netlify site yaratmadi. Token yoki sayt nomini tekshiring.")
            site = site_response.json()
            deploy_response = await client.post(
                f"https://api.netlify.com/api/v1/sites/{site['id']}/deploys",
                headers={**headers, "Content-Type": "application/zip"},
                content=portfolio_zip(document),
            )
            if deploy_response.is_error:
                raise PortfolioDeploymentError("Netlify deploy xatosi yuz berdi.")
            deploy = deploy_response.json()
            url = deploy.get("ssl_url") or deploy.get("deploy_ssl_url") or site.get("ssl_url") or site.get("url")
            if not url:
                raise PortfolioDeploymentError("Netlify javobida sayt manzili topilmadi.")
            return str(url)
    except httpx.HTTPError as error:
        raise PortfolioDeploymentError("Netlify bilan bog‘lanib bo‘lmadi.") from error
