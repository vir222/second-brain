import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import settings
from app.db import get_db
from app.models import User, Notebook

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme), db: Session = Depends(get_db)) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"},)
    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except(jwt.InvalidTokenError, KeyError, ValueError) as e:
        #print("AUTH ERROR", repr(e))
        raise unauthorized

    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user

def get_owned_notebooks(notebook_id: int, user: User, db: Session) -> Notebook:
    notebook = db.scalar(select(Notebook).where(Notebook.id == notebook_id, Notebook.user_id == user.id))
    if notebook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notebook not found")
    return notebook