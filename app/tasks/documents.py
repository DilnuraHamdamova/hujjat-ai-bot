from pathlib import Path
from uuid import UUID

from app.core.config import get_settings
from app.documents.generator import DocumentGenerator
from app.tasks.celery_app import celery_app


@celery_app.task(
    name="documents.generate",
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)  # type: ignore[untyped-decorator]
def generate_documents(resume_id: str, data: dict[str, object]) -> list[dict[str, str]]:
    generator = DocumentGenerator(Path(get_settings().storage_dir))
    artifacts = generator.generate(UUID(resume_id), data)
    return [
        {"format": artifact.format, "path": str(artifact.path), "checksum": artifact.checksum}
        for artifact in artifacts
    ]
