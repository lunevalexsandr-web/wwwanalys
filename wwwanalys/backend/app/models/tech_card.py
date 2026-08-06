"""
Модели базы знаний технологических карт (RAG).

ВАЖНО: этот модуль НЕ импортируется в app/models/__init__.py — он часть
изолированного AI-модуля и подключается только при включённом AI_ENABLED.
Так ядро приложения не зависит от pgvector и не ломается, если расширение/пакет
отсутствуют. Таблицы создаются отдельно в services/rag.py::init_storage().
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, BigInteger
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base
from app.core.config import settings


class TechDocument(Base):
    """Исходный загруженный документ (техкарта сорта и т.п.)."""
    __tablename__ = "tech_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)          # человекочитаемое название
    variety = Column(String(255), nullable=True, index=True)  # сорт (свободно, если задан)
    filename = Column(String(500), nullable=False)
    mime = Column(String(255), nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    sha256 = Column(String(64), nullable=True, index=True)   # дедуп по содержимому
    status = Column(String(50), default="ready")             # ready | processing | error
    char_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    chunks = relationship(
        "TechChunk", back_populates="document", cascade="all, delete-orphan"
    )


class TechChunk(Base):
    """Фрагмент документа в RAG-формате: текст + метаданные + (позже) эмбеддинг."""
    __tablename__ = "tech_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer, ForeignKey("tech_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    char_count = Column(Integer, default=0)
    meta = Column(JSONB, nullable=True)       # {section, page, heading, variety, ...}
    # Эмбеддинг заполняется, когда выбрана эмбеддинг-модель. Пока NULL — поиск по FTS.
    embedding = Column(Vector(settings.embedding_dim), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("TechDocument", back_populates="chunks")
