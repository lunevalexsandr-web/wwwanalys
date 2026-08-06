from sqlalchemy.orm import Session
from typing import List, Optional

from app.models import Variety
from app.schemas import VarietyCreate, VarietyUpdate


def get_varieties(db: Session, active_only: bool = False) -> List[Variety]:
    q = db.query(Variety)
    if active_only:
        q = q.filter(Variety.is_active == True)  # noqa: E712
    return q.order_by(Variety.name).all()


def get_variety(db: Session, variety_id: int) -> Optional[Variety]:
    return db.query(Variety).filter(Variety.id == variety_id).first()


def get_by_external_id(db: Session, external_id: str) -> Optional[Variety]:
    return db.query(Variety).filter(Variety.external_id == external_id).first()


def get_by_name(db: Session, name: str) -> Optional[Variety]:
    return db.query(Variety).filter(Variety.name == name).first()


def create_variety(db: Session, data: VarietyCreate) -> Variety:
    obj = Variety(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_variety(db: Session, variety_id: int, data: VarietyUpdate) -> Optional[Variety]:
    obj = get_variety(db, variety_id)
    if not obj:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_variety(db: Session, variety_id: int) -> bool:
    obj = get_variety(db, variety_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
