from app.db import SessionLocal
from app.models import Document
from app.processing import process_document
from app.worker import celery_app

@celery_app.task
def process_document_task(document_id: int) -> None:
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:
            return
        process_document(db, document)
    finally:
        db.close()
