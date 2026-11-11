from fastapi import APIRouter, Depends, HTTPException, status
from app.deps import get_current_user
from app.schemas import UserOut 
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user