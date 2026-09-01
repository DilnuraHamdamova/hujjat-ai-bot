from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from docx import Document as create_document
from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.services.resume_schema import ResumeData


@dataclass(frozen=True)
class GeneratedArtifact:
    format: str
    path: Path
    checksum: str


class DocumentGenerator:
    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir
        self.template_dir = Path(__file__).resolve().parents[1] / "templates"

    def generate(self, resume_id: UUID, raw_data: dict[str, object]) -> list[GeneratedArtifact]:
        data = ResumeData.model_validate(raw_data)
        output_dir = self.storage_dir / str(resume_id)
        output_dir.mkdir(parents=True, exist_ok=True)

        docx_path = output_dir / "cv.docx"
        pdf_path = output_dir / "cv.pdf"
        self._write_docx(data, docx_path)
        self._write_pdf(data, pdf_path)

        return [
            self._artifact("docx", docx_path),
            self._artifact("pdf", pdf_path),
        ]

    @staticmethod
    def _artifact(file_format: str, path: Path) -> GeneratedArtifact:
        return GeneratedArtifact(
            format=file_format,
            path=path,
            checksum=sha256(path.read_bytes()).hexdigest(),
        )

    @staticmethod
    def _write_docx(data: ResumeData, path: Path) -> None:
        document = create_document()
        styles = document.styles
        styles["Normal"].font.name = "Arial"
        styles["Normal"].font.size = Pt(10)

        title = document.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        name_run = title.add_run(data.full_name or "CV")
        name_run.bold = True
        name_run.font.size = Pt(22)

        position = document.add_paragraph()
        position.alignment = WD_ALIGN_PARAGRAPH.CENTER
        position_run = position.add_run(data.job_title or "")
        position_run.font.size = Pt(13)

        contacts = " | ".join(item for item in (data.phone, data.email, data.location) if item)
        contact_paragraph = document.add_paragraph(contacts)
        contact_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        DocumentGenerator._add_section(document, "PROFIL", [data.summary] if data.summary else [])
        DocumentGenerator._add_section(document, "KO‘NIKMALAR", data.skills)
        DocumentGenerator._add_section(document, "ISH TAJRIBASI", data.experience)
        DocumentGenerator._add_section(document, "TA’LIM", data.education)
        DocumentGenerator._add_section(document, "TILLAR", data.languages)
        document.save(str(path))

    @staticmethod
    def _add_section(document: DocxDocument, title: str, values: list[str]) -> None:
        if not values:
            return
        heading = document.add_paragraph()
        heading_run = heading.add_run(title)
        heading_run.bold = True
        heading_run.font.size = Pt(12)
        for value in values:
            document.add_paragraph(value, style="List Bullet" if len(values) > 1 else None)

    def _write_pdf(self, data: ResumeData, path: Path) -> None:
        from weasyprint import HTML  # type: ignore[import-untyped]

        environment = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(("html", "xml")),
        )
        html = environment.get_template("resume.html").render(resume=data)
        HTML(string=html, base_url=str(self.template_dir)).write_pdf(path)
