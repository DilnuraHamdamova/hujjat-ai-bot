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
