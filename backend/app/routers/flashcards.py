import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, get_owned_notebooks
from app.flashcards import generate_flashcards
from app.models import Document, Flashcard, User
from app.schemas import FlashcardGenerateRequest, FlashcardOut, FlashcardUpdate, ReviewRequest, FlashcardStats
from datetime import datetime, timezone
from app.srs import CardSchedule, schedule_review
from app.rate_limit import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notebooks/{notebook_id}", tags=["flashcards"])

def get_owned_flashcard(notebook_id : int, flashcard_id : int, user: User, db: Session) -> Flashcard:
    notebook = get_owned_notebooks(notebook_id, user, db)
    flashcard = db.scalar(select(Flashcard).join(Document, Flashcard.document_id == Document.id).where(
        Flashcard.id == flashcard_id, Document.notebook_id == notebook.id
    ))
    if flashcard is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Flashcard not found")
    return flashcard

@router.post("/documents/{document_id}/flashcards/generate", response_model=list[FlashcardOut], status_code=status.HTTP_201_CREATED,)
def generate_document_flashcards(notebook_id: int, document_id: int, data: FlashcardGenerateRequest, current_user: User = Depends(rate_limit("flashcards", limit=10, window_seconds=3600)), db: Session = Depends(get_db),):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    document = db.scalar(select(Document).where(Document.id == document_id, Document.notebook_id == notebook.id,))  
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if document.status != "ready":
        raise HTTPException(status.HTTP_409_CONFLICT, "Document has not finished processing.")

    try:
        cards = generate_flashcards(db, document, data.count)
    except Exception:
        logger.exception("Flashcard generation failed for document %s", document.id)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Flashcards could not be generated right now. Try again please.")

    if not cards:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No usable flashcards could be made from this document.",)

    db.add_all(cards)
    db.commit()
    for card in cards:
        db.refresh(card)
    return cards

@router.get("/flashcards/due", response_model=list[FlashcardOut])
def list_due_flashcards(notebook_id : int, limit: int = Query(default=20, ge=1, le=20), current_user : User = Depends(get_current_user), db : Session = Depends(get_db),):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    now = datetime.now(timezone.utc)
    query = (select(Flashcard).join(Document, Flashcard.document_id == Document.id).where(Document.notebook_id == notebook.id, Flashcard.due_at <= now).order_by(Flashcard.due_at, Flashcard.id).limit(limit))
    return db.scalars(query).all()

@router.get("/flashcards/stats", response_model=FlashcardStats)
def flashcard_stats(notebook_id: int, current_user: User = Depends(get_current_user), db : Session = Depends(get_db)):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    now = datetime.now(timezone.utc)

    base = (select(func.count(Flashcard.id)).join(Document, Flashcard.document_id == Document.id).where(Document.notebook_id == notebook.id))
    total = db.scalar(base)
    due = db.scalar(base.where(Flashcard.due_at <= now))
    new = db.scalar(base.where(Flashcard.last_reviewed_at.is_(None)))
    return FlashcardStats(total=total or 0, due=due or 0, new=new or 0)

@router.post("/flashcards/{flashcard_id}/review", response_model=FlashcardOut)
def review_flashcard(notebook_id: int, flashcard_id: int, data: ReviewRequest, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    flashcard = get_owned_flashcard(notebook_id, flashcard_id, current_user, db)
    now = datetime.now(timezone.utc)

    current = CardSchedule(ease_factor=flashcard.ease_factor, interval_days=flashcard.interval_days, repetitions= flashcard.repetitions, due_at=flashcard.due_at,)

    updated = schedule_review(current, data.rating, now)

    flashcard.ease_factor = updated.ease_factor
    flashcard.interval_days = updated.interval_days
    flashcard.repititions = updated.repetitions
    flashcard.due_at = updated.due_at
    flashcard.last_reviewed_at = now

    db.commit()
    db.refresh(flashcard)
    return flashcard

@router.get("/flashcards", response_model=list[FlashcardOut])
def list_flashcards(notebook_id : int, current_user: User = Depends(get_current_user), db : Session = Depends(get_db)):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    query = (select(Flashcard).join(Document, Flashcard.document_id == Document.id).where(Document.notebook_id == notebook.id).order_by(Flashcard.created_at.desc(), Flashcard.id))
    return db.scalars(query).all()

@router.patch("/flashcards/{flashcard_id}", response_model=FlashcardOut)
def update_flashcard(notebook_id: int, flashcard_id: int, data: FlashcardUpdate, current_user : User = Depends(get_current_user), db : Session = Depends(get_db),):
    flashcard = get_owned_flashcard(notebook_id, flashcard_id, current_user, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(flashcard, field, value)
    db.commit()
    db.refresh(flashcard)
    return flashcard

@router.delete("/flashcards/{flashcard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flashcard(notebook_id : int, flashcard_id : int, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    flashcard = get_owned_flashcard(notebook_id, flashcard_id, current_user, db)
    db.delete(flashcard)
    db.commit()

