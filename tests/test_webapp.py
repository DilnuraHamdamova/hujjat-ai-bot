import asyncio

from app.api.routes import template_gallery, template_preview


def test_template_webapp_contains_visible_choices() -> None:
    response = asyncio.run(template_gallery())
    html = response.body.decode()
    assert "Classic" in html
    assert "Zamonaviy" in html
    assert "Europass" in html
    assert "for (let number = 1; number <= 3" in html
    assert 'tg.sendData(JSON.stringify({action: "select_template"' in html


def test_template_preview_only_serves_known_images() -> None:
    response = asyncio.run(template_preview("classic_1.png"))
    assert str(response.path).endswith("classic_1.png")
