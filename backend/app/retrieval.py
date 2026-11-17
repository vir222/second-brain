from sqlalchemy import select
from sqlalchemy.orm import Session
from app.embeddings import embed_texts
from app.models import Chunk, Document
from app.schemas import SearchResult

def search_chunks(db : Session, notebook_id: int, query : str, limit : int) -> list[SearchResult]:
    query_vector = embed_texts([query])[0]
    distance = Chunk.embedding.cosine_distance(query_vector).label("distance")

    statement = (select(Chunk, Document.filename, distance)
                .join(Document, Chunk.document_id == Document.id)
                .where(Document.notebook_id == notebook_id, Document.status == "ready", Chunk.embedding.is_not(None),
                )
                .order_by(distance)
                .limit(limit)
                )

    return [
        SearchResult(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            filename = filename,
            page_number=chunk.page_number,
            content = chunk.content,
            score = round(1-dist, 4),
        )
        for chunk, filename, dist in db.execute(statement).all()
    ]