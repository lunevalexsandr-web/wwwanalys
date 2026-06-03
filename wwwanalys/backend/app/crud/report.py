from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from app.models import AnalysisType, Indicator, ProcessLog, IndicatorValue
from app.schemas import ReportCreate, IndicatorValue as IndicatorValueSchema
from typing import List
from datetime import datetime, date

def create_report(db: Session, report: ReportCreate, user_id: int):
    # Проверяем существование шаблона
    template = db.query(AnalysisType).filter(AnalysisType.id == report.template_id).first()
    if not template:
        return None
    
    try:
        # Создаем отчет (используем ProcessLog, так как IndicatorValue уже используется для индикаторов)
        db_report = ProcessLog(
            batch_number=report.batch_number,
            analysis_type_id=report.template_id,
            created_by=user_id
        )
        db.add(db_report)
        
        # Создаем значения для каждого индикатора
        indicator_values = []
        for value_data in report.values:
            indicator = db.query(Indicator).filter(Indicator.id == value_data.indicator_id).first()
            if not indicator:
                continue
            
            import json
            
            data_type = indicator.data_type
            
            # Подготовка значений для сохранения
            numeric_value = None
            text_value = None
            is_normal = True
            
            if data_type == 'text':
                # Для текстовых индикаторов сохраняем как текст
                text_value = str(value_data.value) if value_data.value is not None else None
                
            elif data_type == 'select':
                # Для select-индикаторов сохраняем выбранное значение как текст
                text_value = str(value_data.value) if value_data.value is not None else None
                # Валидация: проверяем, что значение есть в списке options
                if indicator.options and text_value:
                    try:
                        allowed_options = json.loads(indicator.options)
                        if text_value not in allowed_options:
                            is_normal = False
                    except (json.JSONDecodeError, TypeError):
                        pass
                        
            else:  # DataType.NUMBER
                # Для числовых индикаторов конвертируем в число
                value = value_data.value
                if isinstance(value, str):
                    try:
                        numeric_value = float(value)
                    except ValueError:
                        numeric_value = 0.0
                elif isinstance(value, (int, float)):
                    numeric_value = float(value)
                
                # Проверяем, что значение в допустимом диапазоне
                if numeric_value is not None and indicator.min_value is not None and indicator.max_value is not None:
                    is_normal = indicator.min_value <= numeric_value <= indicator.max_value
            
            db_indicator_value = IndicatorValue(
                indicator_id=value_data.indicator_id,
                value=numeric_value,
                text_value=text_value,
                is_normal=is_normal,
                process_log_id=db_report.id  # ID будет установлен после коммита
            )
            db.add(db_indicator_value)
            indicator_values.append(db_indicator_value)
        
        # Коммитим все за один раз - и ProcessLog, и все IndicatorValue
        db.commit()
        db.refresh(db_report)
        return db_report
        
    except Exception as e:
        # Если что-то пошло не так, откатываем все изменения
        db.rollback()
        raise e

def get_reports(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ProcessLog).offset(skip).limit(limit).all()

def get_report(db: Session, report_id: int):
    return db.query(ProcessLog).options(joinedload(ProcessLog.indicator_values)).filter(ProcessLog.id == report_id).first()

def get_reports_by_template(db: Session, template_id: int):
    return db.query(ProcessLog).filter(ProcessLog.analysis_type_id == template_id).all()

def get_reports_by_user(db: Session, user_id: int):
    return db.query(ProcessLog).filter(ProcessLog.created_by == user_id).all()

def get_reports_filtered(
    db: Session, 
    user_id: int, 
    template_id: int = None, 
    date_from: date = None, 
    date_to: date = None,
    skip: int = 0, 
    limit: int = 100
):
    """Получить отчеты пользователя с фильтрацией по шаблону и дате"""
    query = db.query(ProcessLog).filter(ProcessLog.created_by == user_id)
    
    if template_id:
        query = query.filter(ProcessLog.analysis_type_id == template_id)
    
    if date_from:
        query = query.filter(ProcessLog.started_at >= datetime.combine(date_from, datetime.min.time()))
    
    if date_to:
        query = query.filter(ProcessLog.started_at <= datetime.combine(date_to, datetime.max.time()))
    
    return query.order_by(ProcessLog.started_at.desc()).offset(skip).limit(limit).all()

def delete_all_reports_by_user(db: Session, user_id: int):
    """Удалить все отчеты пользователя"""
    # Сначала удаляем все значения индикаторов
    reports = db.query(ProcessLog).filter(ProcessLog.created_by == user_id).all()
    for report in reports:
        db.query(IndicatorValue).filter(IndicatorValue.process_log_id == report.id).delete()
    
    # Затем удаляем сами отчеты
    db.query(ProcessLog).filter(ProcessLog.created_by == user_id).delete()
    db.commit()
    return {"message": "All reports deleted successfully"}
