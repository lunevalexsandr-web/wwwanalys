from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.auth.auth import get_current_active_user, get_current_admin_user
from app.crud import analysis_type as crud_analysis_type
from app.models import User
from app.schemas import AnalysisType as AnalysisTypeSchema, AnalysisTypeCreate, AnalysisTypeUpdate

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[AnalysisTypeSchema])
def read_analysis_types(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    analysis_types = crud_analysis_type.get_analysis_types(db, skip=skip, limit=limit)
    return analysis_types

@router.get("/{analysis_type_id}", response_model=AnalysisTypeSchema)
def read_analysis_type(analysis_type_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_analysis_type = crud_analysis_type.get_analysis_type(db, analysis_type_id=analysis_type_id)
    if db_analysis_type is None:
        raise HTTPException(status_code=404, detail="Analysis type not found")
    return db_analysis_type

@router.post("/", response_model=AnalysisTypeSchema)
def create_analysis_type(analysis_type: AnalysisTypeCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    return crud_analysis_type.create_analysis_type(db, analysis_type=analysis_type, user_id=current_user.id)

@router.put("/{analysis_type_id}", response_model=AnalysisTypeSchema)
def update_analysis_type(analysis_type_id: int, analysis_type: AnalysisTypeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_analysis_type = crud_analysis_type.update_analysis_type(db, analysis_type_id=analysis_type_id, analysis_type=analysis_type)
    if db_analysis_type is None:
        raise HTTPException(status_code=404, detail="Analysis type not found")
    return db_analysis_type

@router.delete("/{analysis_type_id}")
def delete_analysis_type(analysis_type_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_analysis_type = crud_analysis_type.delete_analysis_type(db, analysis_type_id=analysis_type_id)
    if db_analysis_type is None:
        raise HTTPException(status_code=404, detail="Analysis type not found")
    return {"message": "Analysis type deleted successfully"}

@router.get("/{analysis_type_id}/indicators", response_model=list)
def read_indicators_by_analysis_type(analysis_type_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    indicators = crud_analysis_type.get_indicators_by_analysis_type(db, analysis_type_id=analysis_type_id)
    return indicators