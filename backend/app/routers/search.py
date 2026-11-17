import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import get_current_user, get_owned_notebooks
from app.embeddings import embed_texts
from app.models import Chunk, Document, User
from app.schemas import SearchRequest, SearchResult
from app.retrieval import search_chunks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notebook/{notebook_id}/search", tags = ["search"])

@router.post("", response_model= list[SearchResult])
def search_notebook(notebook_id : int, data : SearchRequest, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    notebook = get_owned_notebooks(notebook_id, current_user, db)

    try:
        return search_chunks(db, notebook.id, data.query, data.limit)
    except Exception:
        logger.exception("Search Failed")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "search is temporarily unavailable. Please try again",)
    