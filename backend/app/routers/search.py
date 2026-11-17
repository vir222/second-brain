import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import get_current_user, get_owned_notebooks
from app.embeddings import embed_texts
from app.models import Chunk, Document, User
from app.schemas import SearchRequest, SearchResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notebook/{notebook_id}/search", tags = ["search"])

@router.post("", response_model= list[SearchResult])
def search_notebook(notebook_id : int, data : SearchRequest, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    notebook = get_owned_notebooks(notebook_id, current_user, db)

    try:
        query_vector = embed_texts([data.query])[0]
    except Exception:
        logger.exception("Failed to embed search query")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "search is temporarily unavailable. Please try again",)
    distance = Chunk.embedding.cosine_distance(query_vector).label("distance")

    query = (select(Chunk, Document.filename, distance).join(Document, Chunk.document_id == Document.id)
                    .where(Document.notebook_id == notebook.id, Document.status == "ready", Chunk.embedding.is_not(None),)
                    .order_by(distance).limit(data.limit)
                    )
    results = []

    for chunk, filename, dist in db.execute(query).all():
        results.append(SearchResult(
            chunk_id = chunk.id,
            document_id=chunk.document_id,
            filename = filename,
            page_number=chunk.page_number,
            content=chunk.content,
            score=round(1-dist,4),
        ))
    return results