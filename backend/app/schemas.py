from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.srs import Rating

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

class AskRequests(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length = 2000)

class Source(SearchResult):
    number : int
    cited : bool

class AskResponse(BaseModel):
    answer : str
    sources : list[Source]

class ConversationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title : str | None = Field(default=None, max_length = 200)

class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id : int
    title : str
    created_at : datetime
    updated_at : datetime

class MessageCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    content : str = Field(min_length=1, max_length=2000)

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id : int
    role : str
    content : str
    sources : list[Source] | None
    created_at : datetime

class ConversationDetail(ConversationOut):
    messages : list[MessageOut]

class GeneratedCard(BaseModel):
    front: str
    back: str
    source_number: int

class GeneratedDeck(BaseModel):
    cards: list[GeneratedCard]

class FlashcardGenerateRequest(BaseModel):
    count: int = Field(default=10, ge=1, le=20)

class FlashcardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    front: str
    back: str
    page_number: int | None
    repetitions : int
    interval_days : int
    due_at : datetime
    last_reviewed_at : datetime | None
    created_at: datetime


class FlashcardUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    front: str | None = Field(default=None, min_length=1, max_length=1000)
    back: str | None = Field(default=None, min_length=1, max_length=2000)
    @field_validator("front", "back")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value

class ReviewRequest(BaseModel):
    rating: Rating

class FlashcardStats(BaseModel):
    total : int
    due : int
    new : int

    
    