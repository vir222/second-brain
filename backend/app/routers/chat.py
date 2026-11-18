import logging
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.llm import generate, generate_stream
from app.db import get_db
from app.deps import get_current_user, get_owned_notebooks
from app.models import User
from app.rag import answer_question, NO_MATCH_ANSWER, SYSTEM_PROMPT, build_context, find_citations
from app.schemas import AskResponse, AskRequests

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notebooks/{notebook_id}", tags = ["chat"])
def sse(event: str, data : dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

@router.post("/ask", response_model=AskResponse)
def ask(notebook_id : int, data : AskRequests, current_user: User = Depends(get_current_user), db : Session = Depends(get_db),):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    try:
        return answer_question(db, notebook.id, data.question)
    except Exception:
        logger.exception("Failed to answer question")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Assistant is temporarily unavailable. Please try again.",)

@router.post("/ask/stream")
def ask_stream(notebook_id : int, data: AskRequests, current_user: User = Depends(get_current_user), db : Session = Depends(get_db),):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    try:
        sources, user_message = build_context(db, notebook.id, data.question)
    except Exception:
        logger.exception("Failed to prepare answer")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "The assistant is temporarily unavailable. Please try again.",
        )

    def event_stream():
        yield sse("sources", {"sources": [s.model_dump() for s in sources]})
        if user_message is None:
            yield sse("delta", {"text": NO_MATCH_ANSWER})
            yield sse("done", {"cited":[]})
            return
        answer_parts : list[str] = []
        try:
            for text in generate_stream(SYSTEM_PROMPT, user_message):
                answer_parts.append(text)
                yield sse("delta", {"text": text})
        except Exception:
            logger.exception("Streaming answer failed")
            yield sse("error", {"message" : "The assitant stopped unexpectedly. Please try again"})
            return

        cited = sorted(find_citations("".join(answer_parts)))
        yield sse("done", {"cited": cited})

    return StreamingResponse(
        event_stream(), 
        media_type="text/event-stream", 
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering" : "no"},
    )
    
    