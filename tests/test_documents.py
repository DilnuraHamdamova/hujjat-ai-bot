from uuid import uuid4

from app.documents.generator import DocumentGenerator


def test_generates_pdf_and_docx(tmp_path) -> None:
    generator = DocumentGenerator(tmp_path)
    artifacts = generator.generate(
        uuid4(),
        {
            "full_name": "Ali Valiyev",
            "job_title": "Backend Developer",
            "phone": "+998 90 123 45 67",
            "email": "ali@example.com",
            "location": "Toshkent",
            "summary": "Ishonchli backend tizimlari yarataman.",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience": ["Example LLC — Backend Developer, 2023–hozir"],
            "education": ["TATU — Dasturiy injiniring"],
            "languages": ["O‘zbek — ona tili", "Ingliz — B2"],
        },
    )
    assert {artifact.format for artifact in artifacts} == {"pdf", "docx"}
    assert all(artifact.path.exists() for artifact in artifacts)
    assert all(artifact.path.stat().st_size > 100 for artifact in artifacts)
    assert all(len(artifact.checksum) == 64 for artifact in artifacts)


def test_generates_only_selected_resume_format_and_templates(tmp_path) -> None:
    for template_code in ("modern", "europass"):
        artifacts = DocumentGenerator(tmp_path).generate(
            uuid4(),
            {
                "document_type": "cv",
                "full_name": "Alice Smith",
                "summary": "Software engineer",
                "custom_sections": [{"title": "Certificates", "content": "Cloud Professional"}],
            },
            "en",
            template_code,
            "pdf",
        )
        assert [artifact.format for artifact in artifacts] == ["pdf"]
        assert artifacts[0].path.name == "cv.pdf"


def test_generates_only_selected_resume_format(tmp_path) -> None:
    artifacts = DocumentGenerator(tmp_path).generate(
        uuid4(),
        {
            "document_type": "cv",
            "full_name": "Alice Smith",
            "summary": "Software engineer",
            "custom_sections": [{"title": "Certificates", "content": "Cloud Professional"}],
        },
        "en",
        "classic",
        "pdf",
    )
    assert [artifact.format for artifact in artifacts] == ["pdf"]
    assert artifacts[0].path.name == "cv.pdf"


def test_generates_objective_docx(tmp_path) -> None:
    artifacts = DocumentGenerator(tmp_path).generate(
        uuid4(),
        {
            "document_type": "objective",
            "objective_full_name": "Ali Valiyev Olimjon o‘g‘li",
            "objective_position": "Example MCHJ direktori",
            "objective_birth_date": "01.01.1990",
            "objective_employment": ["2015–2020 — Mutaxassis"],
            "objective_relatives": ["Otasi | Vali Valiyev | 1960, Toshkent | Nafaqada | Toshkent"],
        },
        "uz",
        file_format="docx",
    )
    assert [artifact.format for artifact in artifacts] == ["docx"]
    assert artifacts[0].path.name == "obyektivka.docx"
    assert artifacts[0].path.stat().st_size > 100


def test_generates_objective_pdf(tmp_path) -> None:
    artifacts = DocumentGenerator(tmp_path).generate(
        uuid4(),
        {
            "document_type": "objective",
            "objective_full_name": "Ali Valiyev",
            "objective_birth_place": "Toshkent",
            "objective_relatives": [
                "Onasi | Valiyeva Lola | 1965, Toshkent | O‘qituvchi | Toshkent"
            ],
        },
        "uz",
        file_format="pdf",
    )
    assert [artifact.format for artifact in artifacts] == ["pdf"]
    assert artifacts[0].path.name == "obyektivka.pdf"
