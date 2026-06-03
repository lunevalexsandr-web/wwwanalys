from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class IndicatorLibraryVersion(Base):
    """История изменений показателей в справочнике."""
    __tablename__ = "indicator_library_versions"

    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(Integer, ForeignKey("indicator_library.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)

    # Снапшот полей показателя на момент версии
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    data_type = Column(String(20), default="number")
    options = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    is_required = Column(Boolean, default=False)
    default_value = Column(String, nullable=True)
    validation_rules = Column(Text, nullable=True)

    # Метаданные версии
    changed_by = Column(Integer, nullable=True)
    change_type = Column(String(20), default="update")  # create | update | delete
    change_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь с показателем
    indicator = relationship("IndicatorLibrary", backref="versions")