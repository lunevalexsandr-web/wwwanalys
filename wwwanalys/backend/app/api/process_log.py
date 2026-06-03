from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.auth.auth import get_current_active_user, get_current_admin_user
from app.crud import process_log as crud_process_log
from app.models import User
from app.schemas import ProcessLog as ProcessLogSchema, ProcessLogCreate, ProcessLogUpdate

router = APIRouter()

@router.get("/", response_model=list[ProcessLogSchema])
def read_process_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    process_logs = crud_process_log.get_process_logs(db, skip=skip, limit=limit)
    return process_logs

@router.get("/{process_log_id}", response_model=ProcessLogSchema)
def read_process_log(process_log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_process_log = crud_process_log.get_process_log(db, process_log_id=process_log_id)
    if db_process_log is None:
        raise HTTPException(status_code=404, detail="Process log not found")
    return db_process_log

@router.post("/", response_model=ProcessLogSchema)
def create_process_log(process_log: ProcessLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return crud_process_log.create_process_log(db, process_log=process_log, user_id=current_user.id)

@router.put("/{process_log_id}", response_model=ProcessLogSchema)
def update_process_log(process_log_id: int, process_log: ProcessLogUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_process_log = crud_process_log.update_process_log(db, process_log_id=process_log_id, process_log=process_log)
    if db_process_log is None:
        raise HTTPException(status_code=404, detail="Process log not found")
    return db_process_log

@router.delete("/{process_log_id}")
def delete_process_log(process_log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_process_log = crud_process_log.delete_process_log(db, process_log_id=process_log_id)
    if db_process_log is None:
        raise HTTPException(status_code=404, detail="Process log not found")
    return {"message": "Process log deleted successfully"}

@router.get("/{process_log_id}/indicator-values", response_model=list)
def read_indicator_values_by_process_log(process_log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    indicator_values = crud_process_log.get_indicator_values_by_process_log(db, process_log_id=process_log_id)
    return indicator_values