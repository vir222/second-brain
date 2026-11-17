from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str 

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class NotebookCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

class NotebookUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_archived: bool | None = Field(default=None)
    @field_validator("title", "is_archived")
    @classmethod
    def validate_null(cls, value):
        if value is None:
            raise ValueError("Title cannot be None")
        return value

class NotebookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime

class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id : int
    notebook_id : int
    filename : str
    content_type : str
    size_bytes : int
    status : str
    error_message: str | None
    created_at : datetime

class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id : int
    chunk_index : int
    page_number : int | None
    content : str

class SearchRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    query : str = Field(min_length=1, max_length=1000)
    limit : int = Field(default=5, ge=1, le=20)

class SearchResult(BaseModel):
    chunk_id : int
    document_id : int
    filename : str
    page_number : int | None
    content : str
    score : float
    