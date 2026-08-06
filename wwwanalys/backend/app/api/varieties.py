"""Справочник сортов: чтение — всем авторизованным, изменение — админ."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import variety as crud_variety
from app.models import User
from app.schemas import VarietySchema, VarietyCreate, VarietyUpdate
from app.auth.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.get("", response_model=List[VarietySchema])
@router.get("/", response_model=List[VarietySchema])
def list_varieties(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_variety.get_varieties(db, active_only=active_only)


@router.post("/", response_model=VarietySchema)
def create_variety(
    data: VarietyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    if crud_variety.get_by_name(db, data.name):
        raise HTTPException(status_code=400, detail="Сорт с таким названием уже существует")
    return crud_variety.create_variety(db, data)


@router.put("/{variety_id}", response_model=VarietySchema)
def update_variety(
    variety_id: int,
    data: VarietyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    obj = crud_variety.update_variety(db, variety_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Сорт не найден")
    return obj


@router.delete("/{variety_id}")
def delete_variety(
    variety_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    if not crud_variety.delete_variety(db, variety_id):
        raise HTTPException(status_code=404, detail="Сорт не найден")
    return {"deleted": variety_id}
