from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from docx import Document as create_document
from docx.document import Document as DocxDocument
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.services.localization import DOCUMENT_LABELS, OBJECTIVE_LABELS, normalize_language
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

    def generate(
        self,
        resume_id: UUID,
        raw_data: dict[str, object],
        language: str = "uz",
        template_code: str = "classic",
        file_format: str | None = None,
    ) -> list[GeneratedArtifact]:
        locale = normalize_language(language)
        output_dir = self.storage_dir / str(resume_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        document_type = str(raw_data.get("document_type", "cv"))
        basename = "obyektivka" if document_type == "objective" else "cv"
        formats = (file_format,) if file_format in ("pdf", "docx") else ("docx", "pdf")
        artifacts: list[GeneratedArtifact] = []
        for selected_format in formats:
            path = output_dir / f"{basename}.{selected_format}"
            if document_type == "objective":
                if selected_format == "docx":
                    self._write_objective_docx(raw_data, path, locale)
                else:
                    self._write_objective_pdf(raw_data, path, locale)
            else:
                data = ResumeData.model_validate(raw_data)
                if selected_format == "docx":
                    self._write_resume_docx(data, raw_data, path, locale, template_code)
                else:
                    self._write_resume_pdf(data, raw_data, path, locale, template_code)
            artifacts.append(self._artifact(selected_format, path))
        return artifacts

    @staticmethod
    def _artifact(file_format: str, path: Path) -> GeneratedArtifact:
        return GeneratedArtifact(
            format=file_format,
            path=path,
            checksum=sha256(path.read_bytes()).hexdigest(),
        )

    @staticmethod
    def _write_resume_docx(
        data: ResumeData,
        raw_data: dict[str, object],
        path: Path,
        language: str,
        template_code: str,
    ) -> None:
        labels = DOCUMENT_LABELS[normalize_language(language)]
        document = create_document()
        styles = document.styles
        styles["Normal"].font.name = "Arial"
        styles["Normal"].font.size = Pt(10)

        photo_path = Path(str(raw_data.get("photo_path", "")))
        if photo_path.is_file():
            photo = document.add_paragraph()
            photo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            photo.add_run().add_picture(str(photo_path), width=Inches(1.18), height=Inches(1.57))

        title = document.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        name_run = title.add_run(data.full_name or "CV")
        name_run.bold = True
        name_run.font.size = Pt(22)
        if template_code == "europass":
            name_run.font.color.rgb = RGBColor(28, 83, 145)
        elif template_code == "modern":
            name_run.font.color.rgb = RGBColor(13, 148, 136)

        position = document.add_paragraph()
        position.alignment = WD_ALIGN_PARAGRAPH.CENTER
        position_run = position.add_run(data.job_title or "")
        position_run.font.size = Pt(13)

        contacts = " | ".join(item for item in (data.phone, data.email, data.location) if item)
        contact_paragraph = document.add_paragraph(contacts)
        contact_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        DocumentGenerator._add_section(
            document, labels["profile"], [data.summary] if data.summary else []
        )
        DocumentGenerator._add_section(document, labels["skills"], data.skills)
        DocumentGenerator._add_section(document, labels["experience"], data.experience)
        DocumentGenerator._add_section(document, labels["education"], data.education)
        DocumentGenerator._add_section(document, labels["languages"], data.languages)
        DocumentGenerator._add_custom_docx_sections(document, raw_data)
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

    @staticmethod
    def _add_custom_docx_sections(document: DocxDocument, raw_data: dict[str, object]) -> None:
        raw_sections = raw_data.get("custom_sections", [])
        if not isinstance(raw_sections, list):
            return
        for section in raw_sections:
            if not isinstance(section, dict):
                continue
            title = str(section.get("title", "")).strip()
            content = str(section.get("content", "")).strip()
            if title and content:
                DocumentGenerator._add_section(document, title.upper(), [content])

    def _environment(self) -> Environment:
        return Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(("html", "xml")),
        )

    def _write_resume_pdf(
        self,
        data: ResumeData,
        raw_data: dict[str, object],
        path: Path,
        language: str,
        template_code: str,
    ) -> None:
        from weasyprint import HTML  # type: ignore[import-untyped]

        labels = DOCUMENT_LABELS[normalize_language(language)]
        templates = {
            "classic": "resume.html",
            "modern": "resume_modern.html",
            "europass": "resume_europass.html",
        }
        template_name = templates.get(template_code, "resume.html")
        photo_path = Path(str(raw_data.get("photo_path", "")))
        html = (
            self._environment()
            .get_template(template_name)
            .render(
                resume=data,
                language=language,
                labels=labels,
                custom_sections=raw_data.get("custom_sections", []),
                photo_uri=photo_path.resolve().as_uri() if photo_path.is_file() else "",
            )
        )
        HTML(string=html, base_url=str(self.template_dir)).write_pdf(path)

    def _write_objective_docx(self, data: dict[str, object], path: Path, language: str) -> None:
        labels = OBJECTIVE_LABELS[normalize_language(language)]
        document = create_document()
        document.sections[0].top_margin = Inches(0.55)
        document.sections[0].bottom_margin = Inches(0.55)

        title = document.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.add_run(labels["document_title"])
        run.bold = True
        run.font.size = Pt(16)

        photo_path = Path(str(data.get("photo_path", "")))
        if photo_path.is_file():
            photo = document.add_paragraph()
            photo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            photo.add_run().add_picture(str(photo_path), width=Inches(1.18), height=Inches(1.57))

        full_name = str(data.get("objective_full_name", ""))
        heading = document.add_paragraph()
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        heading_run = heading.add_run(full_name)
        heading_run.bold = True
        heading_run.font.size = Pt(14)

        field_map = (
            ("objective_position", "position"),
            ("objective_birth_date", "birth_date"),
            ("objective_birth_place", "birth_place"),
            ("objective_nationality", "nationality"),
            ("objective_party", "party"),
            ("objective_education_level", "education_level"),
            ("objective_graduated", "graduated"),
            ("objective_specialty", "specialty"),
            ("objective_degree", "degree"),
            ("objective_title", "academic_title"),
            ("objective_languages", "foreign_languages"),
            ("objective_awards", "awards"),
            ("objective_elected", "elected"),
        )
        table = document.add_table(rows=0, cols=2)
        table.style = "Table Grid"
        for key, label_key in field_map:
            if key not in data:
                continue
            row = table.add_row().cells
            row[0].text = labels[label_key]
            value = data[key]
            row[1].text = "\n".join(map(str, value)) if isinstance(value, list) else str(value)

        employment = data.get("objective_employment")
        if isinstance(employment, list) and employment:
            DocumentGenerator._add_section(
                document, labels["employment"], list(map(str, employment))
            )
        DocumentGenerator._add_custom_docx_sections(document, data)

        relatives = data.get("objective_relatives")
        if isinstance(relatives, list) and relatives:
            document.add_section(WD_SECTION.NEW_PAGE)
            DocumentGenerator._add_relatives_docx(document, list(map(str, relatives)), labels)
        document.save(str(path))

    @staticmethod
    def _add_relatives_docx(
        document: DocxDocument, relatives: list[str], labels: dict[str, str]
    ) -> None:
        heading = document.add_paragraph()
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = heading.add_run(labels["relatives"])
        run.bold = True
        table = document.add_table(rows=1, cols=5)
        table.style = "Table Grid"
        headers = (
            labels["relationship"],
            labels["relative_name"],
            labels["relative_birth"],
            labels["relative_work"],
            labels["relative_address"],
        )
        for cell, header in zip(table.rows[0].cells, headers, strict=True):
            cell.text = header
        for relative in relatives:
            parts = [part.strip() for part in relative.split("|")]
            parts.extend([""] * (5 - len(parts)))
            cells = table.add_row().cells
            for cell, value in zip(cells, parts[:5], strict=True):
                cell.text = value

    def _write_objective_pdf(self, data: dict[str, object], path: Path, language: str) -> None:
        from weasyprint import HTML

        labels = OBJECTIVE_LABELS[normalize_language(language)]
        photo_path = Path(str(data.get("photo_path", "")))
        relatives = []
        raw_relatives = data.get("objective_relatives", [])
        if isinstance(raw_relatives, list):
            for relative in raw_relatives:
                parts = [part.strip() for part in str(relative).split("|")]
                parts.extend([""] * (5 - len(parts)))
                relatives.append(parts[:5])
        html = (
            self._environment()
            .get_template("objective.html")
            .render(
                data=data,
                language=language,
                labels=labels,
                photo_uri=photo_path.resolve().as_uri() if photo_path.is_file() else "",
                relatives=relatives,
                custom_sections=data.get("custom_sections", []),
            )
        )
        HTML(string=html, base_url=str(self.template_dir)).write_pdf(path)
