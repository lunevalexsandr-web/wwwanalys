"""Справочник сортов (пива). Может наполняться из 1С по OData."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone

from app.core.database import Base


class Variety(Base):
    __tablename__ = "varieties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    code = Column(String(100), nullable=True)                 # артикул/код из 1С
    description = Column(String, nullable=True)
    external_id = Column(String(255), nullable=True, unique=True, index=True)  # Ref_Key из 1С
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
