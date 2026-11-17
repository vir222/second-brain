import logging
from pathlib import Path
from pypdf import PdfReader
from sqlalchemy import delete
from sqlalchemy.orm import Session
from app import storage
from app.models import Chunk, Document
from app.embeddings import embed_texts

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

class ProcessingError(Exception):
    """A problem with the file that we can explain to user"""

def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    return " ".join(text.split())

def extract_pages(path: Path, content_type: str) -> list[tuple[int | None, str]]:
    if content_type == "application/pdf":
        try:
            reader = PdfReader(path)
        except Exception as e:
            raise ProcessingError("This PDF could not be read or is damaged") from e
        if reader.is_encrypted:
            raise ProcessingError("Pasword-protected PDFs aren't supported")
        return [(page_number, page.extract_text() or "") for page_number, page in enumerate(reader.pages, start=1)]
    return [(None, path.read_text(encoding="utf-8"))]

def chunk_text(text: str, chunk_size : int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    text = clean_text(text)
    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary

        chunks.append(text[start:end].strip())

        if end >= len(text):
            break

        space = text.find(" ", end - overlap, end)
        next_start = space + 1 if space != -1 else end
        start = next_start if next_start > start else end

    return [c for c in chunks if c]

def process_document(db: Session, document: Document) -> None:
    document.status = "processing"
    document.error_message = None
    db.commit()

    try:
        db.execute(delete(Chunk).where(Chunk.document_id == document.id))
        pages = extract_pages(storage.get_path(document.storage_key), document.content_type)
        #chunk_index = 0
        chunks : list[Chunk] = []
        for page_number, page_text in pages:
            for content in chunk_text(page_text):
                chunks.append(Chunk(
                    document_id=document.id,
                    chunk_index=len(chunks),
                    page_number=page_number,
                    content=content,
                ))


        if not chunks:
            raise ProcessingError("no text could be found, (if pdf its an image not text)")
        vectors = embed_texts([chunk.content for chunk in chunks])
        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk.embedding = vector
        db.add_all(chunks)
        document.status = "ready"
        db.commit()
    except Exception as e:
        db.rollback()
        if isinstance(e, ProcessingError):
            message = str(e)
        else:
            logger.exception("failed to process document %s", document.id)
            message = "something went wrong while processing this file."
        document.status = "failed"
        document.error_message = message
        db.commit()
    