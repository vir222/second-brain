from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app import storage
from app.config import settings
from app.db import get_db
from app.deps import get_owned_notebooks, get_current_user
from app.models import Document, User, Chunk
from app.schemas import DocumentOut, ChunkOut
from app.processing import process_document

router = APIRouter(prefix="/notebooks/{noteboook_id}/documents", tags = ["documents"])

ALLOWED_TYPES = {
    ".pdf" : "application/pdf",
    ".txt" : "text/plain",
    ".md" : "text/markdown",
}

def get_owned_document(notebook_id : int, document_id: int, user : User, db: Session) -> Document:
    notebook = get_owned_notebooks(notebook_id, user, db)
    document = db.scalar(select(Document).where(Document.id == document_id, Document.notebook_id  == notebook.id))
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return document

def validate_contents(extension: str, data : bytes) -> None:
    if extension == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "File is not pdf")
    else:
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "txt files must be utf-8")

@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(notebook_id : int, file : UploadFile, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    filename = file.filename or "untitled"
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported file type. (.pdf, .txt, or .md file)")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"file is larger than {settings.max_upload_mb} MB")
    if len(data) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty file")

    validate_contents(extension, data)
    key = storage.save_file(data, extension)
    document = Document(
        notebook_id = notebook.id,
        filename = filename[:255],
        storage_key=key,
        content_type=ALLOWED_TYPES[extension],
        size_bytes=len(data)
    )
    db.add(document)
    try:
        db.commit()
    except Exception:
        storage.delete_file(key)
        raise
    db.refresh(document)
    process_document(db, document)
    db.refresh(document)
    return document

@router.get("", response_model=list[DocumentOut])
def list_documents(notebook_id : int, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    query = (select(Document).where(Document.notebook_id == notebook.id).order_by(Document.created_at.desc()))
    return db.scalars(query).all()

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(notebook_id : int, document_id : int, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    document = get_owned_document(notebook_id, document_id, current_user, db)
    key = document.storage_key
    db.delete(document)
    db.commit()
    storage.delete_file(key)

@router.get("/{document_id}/chunks", response_model=list[ChunkOut])
def list_chunks(notebook_id : int, document_id : int, current_user : User = Depends(get_current_user), db : Session = Depends(get_db),):
    document = get_owned_document(notebook_id, document_id, current_user, db)
    query = (select(Chunk).where(Chunk.document_id == document.id).order_by(Chunk.chunk_index))
    return db.scalars(query).all()

