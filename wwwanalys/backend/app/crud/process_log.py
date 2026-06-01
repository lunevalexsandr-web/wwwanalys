from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.models import ProcessLog, IndicatorValue
from app.schemas import ProcessLogCreate, ProcessLogUpdate
from datetime import datetime
from app.models.process_log import Status

def get_process_log(db: Session, process_log_id: int):
    return db.query(ProcessLog).options(
        joinedload(ProcessLog.analysis_type),
        joinedload(ProcessLog.creator),
        joinedload(ProcessLog.indicator_values)
    ).filter(ProcessLog.id == process_log_id).first()

def get_process_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ProcessLog).options(
        joinedload(ProcessLog.analysis_type),
        joinedload(ProcessLog.creator),
        joinedload(ProcessLog.indicator_values)
    ).offset(skip).limit(limit).all()

def create_process_log(db: Session, process_log: ProcessLogCreate, user_id: int):
    db_process_log = ProcessLog(
        batch_number=process_log.batch_number,
        analysis_type_id=process_log.analysis_type_id,
        created_by=user_id,
        status=process_log.status,
        notes=process_log.notes
    )
    db.add(db_process_log)
    db.commit()
    db.refresh(db_process_log)
    
    # Добавляем значения индикаторов, если они есть
    if process_log.indicator_values:
        for value_data in process_log.indicator_values:
            indicator_value = IndicatorValue(
                process_log_id=db_process_log.id,
                indicator_id=value_data.indicator_id,
                value=value_data.value
            )
            db.add(indicator_value)
        
        db.commit()
        db.refresh(db_process_log)
    
    return db_process_log

def update_process_log(db: Session, process_log_id: int, process_log: ProcessLogUpdate):
    db_process_log = get_process_log(db, process_log_id=process_log_id)
    if db_process_log:
        update_data = process_log.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_process_log, field, value)
        
        # Если статус меняется на COMPLETED, устанавливаем время завершения
        if process_log.status == Status.COMPLETED and db_process_log.status != Status.COMPLETED:
            db_process_log.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_process_log)
    return db_process_log

def delete_process_log(db: Session, process_log_id: int):
    db_process_log = get_process_log(db, process_log_id=process_log_id)
    if db_process_log:
        # Сначала удаляем связанные значения индикаторов
        for value in db_process_log.indicator_values:
            db.delete(value)
        
        # Затем удаляем запись журнала
        db.delete(db_process_log)
        db.commit()
    return db_process_log

def get_indicator_values_by_process_log(db: Session, process_log_id: int):
    return db.query(IndicatorValue).filter(IndicatorValue.process_log_id == process_log_id).all()