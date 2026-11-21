from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Boolean, func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB

EMBEDDING_DIMENSIONS = 1536

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notebooks : Mapped[list["Notebook"]] = relationship(back_populates="owner", cascade="all, delete-orphan")

class Notebook(Base):
    __tablename__ = "notebooks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    owner: Mapped["User"] = relationship(back_populates="notebooks")
    is_archived: Mapped[bool] = mapped_column(Boolean, server_default="false")
    documents: Mapped[list["Document"]] = relationship(back_populates="notebook", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="notebook", cascade="all, delete-orphan")   

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(ForeignKey("notebooks.id", ondelete="CASCADE"), index = True)
    filename : Mapped[str] = mapped_column(String(255))
    storage_key : Mapped[str] = mapped_column(String(255), unique=True)
    content_type : Mapped[str] = mapped_column(String(100))
    size_bytes : Mapped[int]
    status : Mapped[str] = mapped_column(String(20), server_default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    notebook: Mapped["Notebook"] = relationship(back_populates="documents")
    chunks : Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    flashcards: Mapped[list["Flashcard"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index"), Index(
        "ix_chunks_embedding_hnsw", "embedding", postgresql_using="hnsw", postgresql_ops={"embedding":"vector_cosine_ops"},
    ),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    chunk_index : Mapped[int]
    page_number: Mapped[int | None]
    content : Mapped[str] = mapped_column(Text)
    document : Mapped["Document"] = relationship(back_populates="chunks")
    embedding : Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS))

class Conversation(Base):
    __tablename__ = "conversations"

    id : Mapped[int] = mapped_column(primary_key=True)
    notebook_id: Mapped[int] = mapped_column(ForeignKey("notebooks.id", ondelete="CASCADE"), index=True)
    title : Mapped[str] = mapped_column(String(200), server_default="New Conversation")
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    notebook : Mapped["Notebook"] = relationship(back_populates="conversations")
    messages : Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="Message.id",)

class Message(Base):
    __tablename__ = "messages"
    id : Mapped[int] = mapped_column(primary_key=True)
    conversation_id : Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role : Mapped[str] = mapped_column(String(20))
    content : Mapped[str] = mapped_column(Text)
    sources : Mapped[list[dict] | None] = mapped_column(JSONB)
    created_at : Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    conversation : Mapped["Conversation"] = relationship(back_populates="messages")

class Flashcard(Base):
    __tablename__ = "flashcards"

    id : Mapped[int] = mapped_column(primary_key=True)
    document_id : Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index = True)
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    document: Mapped["Document"] = relationship(back_populates="flashcards")
    ease_factor: Mapped[float] = mapped_column(server_default="2.5")
    interval_days: Mapped[int] = mapped_column(server_default="0")
    repetitions: Mapped[int] = mapped_column(server_default="0")
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

