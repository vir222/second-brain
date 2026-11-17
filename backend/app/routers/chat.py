import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import get_current_user, get_owned_notebooks
from app.models import User
from app.rag import answer_question
from app.schemas import AskResponse, AskRequests

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notebooks/{notebook_id}", tags = ["chat"])

@router.post("/ask", response_model=AskResponse)
def ask(notebook_id : int, data : AskRequests, current_user: User = Depends(get_current_user), db : Session = Depends(get_db),):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    try:
        return answer_question(db, notebook.id, data.question)
    except Exception:
        logger.exception("Failed to answer question")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Assistant is temporarily unavailable. Please try again.",)
    