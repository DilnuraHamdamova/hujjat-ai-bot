from app.services.resume_schema import ResumeData


def test_resume_schema_normalizes_string_lists() -> None:
    resume = ResumeData.model_validate(
        {"full_name": "Ali Valiyev", "skills": "Python, FastAPI", "languages": None}
    )
    assert resume.skills == ["Python", "FastAPI"]
    assert resume.languages == []
