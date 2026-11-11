from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import get_current_user
from app.models import User, Notebook
from app.schemas import NotebookCreate, NotebookOut, NotebookUpdate

router = APIRouter(prefix="/notebooks", tags=["notebooks"])

def get_owned_notebooks(notebook_id: int, user: User, db: Session) -> Notebook:
    notebook = db.scalar(select(Notebook).where(Notebook.id == notebook_id, Notebook.user_id == user.id))
    if notebook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notebook not found")
    return notebook

@router.post("", response_model=NotebookOut, status_code=status.HTTP_201_CREATED)
def create_notebook(data: NotebookCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notebook = Notebook(**data.model_dump(), user_id=current_user.id)
    db.add(notebook)
    db.commit()
    db.refresh(notebook)
    return notebook

@router.get("", response_model=list[NotebookOut])
def list_notebooks(include_archived: bool = False, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = select(Notebook).where(Notebook.user_id == current_user.id)
    if not include_archived:
        query = query.where(Notebook.is_archived == False)
    query = query.order_by(Notebook.created_at.desc())
    return db.scalars(query).all()

@router.get("/{notebook_id}", response_model=NotebookOut)
def get_notebook(notebook_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    return notebook

@router.patch("/{notebook_id}", response_model=NotebookOut)
def update_notebook(notebook_id: int, data: NotebookUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(notebook, field, value)
    db.commit()
    db.refresh(notebook)
    return notebook

@router.delete("/{notebook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notebook(notebook_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notebook = get_owned_notebooks(notebook_id, current_user, db)
    db.delete(notebook)
    db.commit()
    return