import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from app.documents.generator import DocumentGenerator

SAMPLE_DATA: dict[str, object] = {
    "document_type": "cv",
    "full_name": "Aziza Karimova",
    "job_title": "Product Designer",
    "phone": "+998 90 123 45 67",
    "email": "aziza@example.com",
    "location": "Toshkent, O‘zbekiston",
    "summary": (
        "Foydalanuvchiga qulay raqamli mahsulotlarni tadqiqot, prototiplash "
        "va dizayn tizimlari orqali yarataman."
    ),
    "skills": ["Figma", "UX Research", "Prototyping", "Design Systems"],
    "experience": [
        "2023–hozir — Senior Product Designer, Example Tech",
        "2020–2023 — UI/UX Designer, Digital Studio",
    ],
    "education": ["2016–2020 — TATU, Dasturiy injiniring"],
    "languages": ["O‘zbek — ona tili", "Ingliz — C1", "Rus — B2"],
    "custom_sections": [
        {"title": "Sertifikatlar", "content": "Google UX Design Professional Certificate"}
    ],
}


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "app" / "assets" / "template_previews"
    output_dir.mkdir(parents=True, exist_ok=True)
    sample_data = dict(SAMPLE_DATA)
    sample_data["photo_path"] = str(output_dir / "sample-profile.png")

    with tempfile.TemporaryDirectory(prefix="hujjatai-previews-") as temp_dir:
        generator = DocumentGenerator(Path(temp_dir))
        for template_code in ("classic", "modern", "europass"):
            artifact = generator.generate(
                uuid4(),
                sample_data,
                "uz",
                template_code,
                "pdf",
            )[0]
            subprocess.run(
                [
                    "pdftoppm",
                    "-png",
                    "-f",
                    "1",
                    "-singlefile",
                    "-r",
                    "90",
                    str(artifact.path),
                    str(output_dir / template_code),
                ],
                check=True,
            )


if __name__ == "__main__":
    main()
