import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db import get_db, SessionLocal
from app.deps import get_owned_notebooks, get_current_user, get_owned_conversation
from app.llm import generate_stream
from app.models import Conversation, Message, User, Notebook
from app.rag import (NO_MATCH_ANSWER, SYSTEM_PROMPT, build_context, build_history, find_citations, rewrite_query)
from app.schemas import (ConversationOut, ConversationCreate, ConversationDetail, MessageOut, MessageCreate)
from app.rate_limit import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notebooks/{notebook_id}/conversations", tags=["conversations"])

DEFAULT_TITLE = "New conversation"

def sse(event : str, data : dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(notebook_id : int, data: ConversationCreate, current_user : User = Depends(get_current_user), db : Session = Depends(get_db),):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    conversation = Conversation(notebook_id=notebook.id, title=data.title or DEFAULT_TITLE)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

@router.get("", response_model=list[ConversationOut])
def list_conversation(notebook_id : int, current_user : User = Depends(get_current_user), db : Session = Depends(get_db),):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    query = (select(Conversation).where(Conversation.notebook_id == notebook.id).order_by(Conversation.updated_at.desc()))
    return db.scalars(query).all()

@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(notebook_id : int, conversation_id : int, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    return get_owned_conversation(notebook_id, conversation_id, current_user, db)

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(notebook_id: int, conversation_id: int, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    conversation = get_owned_conversation(notebook_id, conversation_id, current_user, db)
    db.delete(conversation)
    db.commit()

@router.post("/{conversation_id}/messages/stream")
def send_message_stream(notebook_id: int, conversation_id : int, data: MessageCreate, current_user : User = Depends(rate_limit("chat", limit=30, window_seconds=3600)), db : Session = Depends(get_db)):
    conversation = get_owned_conversation(notebook_id, conversation_id, current_user, db)
    history = build_history(conversation.messages)
    logger.info("History messages: %d", len(history))

    try:
        search_query = rewrite_query(history, data.content)
        logger.info("Search Query: %r", search_query)
        sources, user_message = build_context(db, conversation.notebook_id, search_query, data.content)
    except Exception:
        logger.exception("Failed to prepare answer")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Assistant is temporarily unavailable. Please try again.")

    db.add(Message(conversation_id=conversation_id, role="user", content = data.content))
    if conversation.title == DEFAULT_TITLE:
        conversation.title = data.content[:60]
    conversation.updated_at = func.now()
    db.commit()
    conversation_id_value = conversation.id
    claude_messages = history + [{"role" : "user", "content" : user_message}] if user_message else []

    def save_assistant_message(content: str, cited: list[int]) -> int:
        saved_sources = [
            {**source.model_dump(), "cited" : source.number in cited} for source in sources
        ]
        with SessionLocal() as session:
            message = Message(
                conversation_id = conversation_id_value,
                role = "assistant",
                content = content,
                sources=saved_sources,
            )
            session.add(message)
            session.commit()
            return message.id
    def event_stream():
        yield sse("sources", {"sources": [s.model_dump() for s in sources]})
        if user_message is None:
            yield sse("delta", {"text" : NO_MATCH_ANSWER})
            message_id = save_assistant_message(NO_MATCH_ANSWER, [])
            yield sse("done", {"cited" : [], "message_id": message_id})
            return
        answer_parts: list[str] = []
        try:
            for text in generate_stream(SYSTEM_PROMPT, claude_messages):
                answer_parts.append(text)
                yield sse("delta", {"text" : text})
        except Exception:
            logger.exception("Streaming answer failed")
            yield sse("error", {"message": "The assistant stopped unexpectedly. Please try again."})
            return

        answer = "".join(answer_parts)
        cited = sorted(find_citations(answer))
        try:
            message_id = save_assistant_message(answer, cited)
        except Exception:
            logger.exception("Failed to save assistance message")
            yield sse("error", {"message": "The answer could not be saved."})
            return
        yield sse("done", {"cited" : cited, "message_id" : message_id})
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},)
