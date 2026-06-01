from sqlalchemy.orm import Session
from app.models import AnalysisType, Indicator, ProcessLog, IndicatorValue
from app.schemas import ReportCreate, IndicatorValue as IndicatorValueSchema
from typing import List

def create_report(db: Session, report: ReportCreate, user_id: int):
    # Проверяем существование шаблона
    template = db.query(AnalysisType).filter(AnalysisType.id == report.template_id).first()
    if not template:
        return None
    
    # Создаем отчет (используем ProcessLog, так как IndicatorValue уже используется для индикаторов)
    db_report = ProcessLog(
        batch_number=report.batch_number,
        analysis_type_id=report.template_id,
        created_by=user_id
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # Создаем значения для каждого индикатора
    indicator_values = []
    for value_data in report.values:
        indicator = db.query(Indicator).filter(Indicator.id == value_data.indicator_id).first()
        if not indicator:
            continue
            
        # Проверяем, что значение в допустимом диапазоне
        is_normal = indicator.min_value <= value_data.value <= indicator.max_value
        
        db_indicator_value = IndicatorValue(
            indicator_id=value_data.indicator_id,
            value=value_data.value,
            is_normal=is_normal,
            process_log_id=db_report.id
        )
        db.add(db_indicator_value)
        indicator_values.append(db_indicator_value)
    
    db.commit()
    return db_report

def get_reports(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ProcessLog).offset(skip).limit(limit).all()

def get_report(db: Session, report_id: int):
    return db.query(ProcessLog).filter(ProcessLog.id == report_id).first()

def get_reports_by_template(db: Session, template_id: int):
    return db.query(ProcessLog).filter(ProcessLog.analysis_type_id == template_id).all()

def get_reports_by_user(db: Session, user_id: int):
    return db.query(ProcessLog).filter(ProcessLog.created_by == user_id).all()