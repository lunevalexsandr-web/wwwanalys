from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from app.models import AnalysisType, IndicatorLibrary, ProcessLog, IndicatorValue, TemplateIndicator, PlanItem
from app.schemas import ReportCreate, IndicatorValue as IndicatorValueSchema
from typing import List
from datetime import datetime, date

def create_report(db: Session, report: ReportCreate, user_id: int):
    # Проверяем существование шаблона
    template = db.query(AnalysisType).filter(AnalysisType.id == report.template_id).first()
    if not template:
        return None
    
    try:
        # Если передан plan_item_id, берём batch_number из PlanItem (приоритетнее frontend)
        batch_number = report.batch_number
        if report.plan_item_id:
            plan_item = db.query(PlanItem).filter(PlanItem.id == report.plan_item_id).first()
            if plan_item and plan_item.batch_number:
                batch_number = plan_item.batch_number

        # Создаем отчет
        db_report = ProcessLog(
            batch_number=batch_number,
            variety=report.variety,
            container=report.container,
            object_key=report.object_key,
            analysis_type_id=report.template_id,
            created_by=user_id
        )
        db.add(db_report)
        db.flush()  # Получаем ID отчета до коммита
        
        # Создаем значения для каждого индикатора
        for value_data in report.values:
            # Ищем показатель в справочнике
            lib_indicator = db.query(IndicatorLibrary).filter(
                IndicatorLibrary.id == value_data.indicator_id
            ).first()
            
            if not lib_indicator:
                continue
            
            # Нормы: сначала из матрицы (день+сорт+тара), фолбэк на TemplateIndicator
            from app.services.norms import resolve_norm, variety_key_by_name
            vday = getattr(value_data, "day", None)
            norm = resolve_norm(
                db, report.template_id, value_data.indicator_id,
                day=vday, container=report.container,
                variety_key=variety_key_by_name(db, report.variety),
                object_key=report.object_key,
            )
            if norm is not None and (norm.min_value is not None or norm.max_value is not None):
                min_value, max_value = norm.min_value, norm.max_value
            else:
                template_indicator = db.query(TemplateIndicator).filter(
                    TemplateIndicator.indicator_id == value_data.indicator_id,
                    TemplateIndicator.template_id == report.template_id
                ).first()
                min_value = template_indicator.min_value if template_indicator else None
                max_value = template_indicator.max_value if template_indicator else None

            data_type = lib_indicator.data_type
            options = lib_indicator.options

            import json

            # Подготовка значений для сохранения
            numeric_value = None
            text_value = None
            is_normal = True
            
            if data_type == 'text':
                # Для текстовых показателей сохраняем как текст
                text_value = str(value_data.value) if value_data.value is not None else None
                
            elif data_type == 'select':
                # Для select-показателей сохраняем выбранное значение как текст.
                # Отклонение определяется ТОЛЬКО по эталону (norm_text ниже),
                # а не по членству в options — options это лишь варианты выбора.
                text_value = str(value_data.value) if value_data.value is not None else None

            else:  # number
                # Для числовых показателей конвертируем в число
                value = value_data.value
                if isinstance(value, str):
                    try:
                        numeric_value = float(value)
                    except ValueError:
                        numeric_value = 0.0
                elif isinstance(value, (int, float)):
                    numeric_value = float(value)
                
                # Проверяем, что значение в допустимом диапазоне
                if numeric_value is not None and min_value is not None and max_value is not None:
                    is_normal = min_value <= numeric_value <= max_value
            
            # Нечисловая норма (список/строка): отклонение, если значение не совпало с эталоном
            if data_type in ('text', 'select') and norm is not None and getattr(norm, 'norm_text', None) and text_value:
                if str(text_value).strip().lower() != str(norm.norm_text).strip().lower():
                    is_normal = False

            db_indicator_value = IndicatorValue(
                indicator_id=value_data.indicator_id,
                value=numeric_value,
                text_value=text_value,
                day=vday,
                is_normal=is_normal,
                process_log_id=db_report.id
            )
            db.add(db_indicator_value)
        
        # Если отчет создан из элемента плана - обновляем связь
        if report.plan_item_id:
            plan_item = db.query(PlanItem).filter(PlanItem.id == report.plan_item_id).first()
            if plan_item:
                plan_item.completed_report_id = db_report.id
                plan_item.is_completed = True
                plan_item.batch_number = batch_number
        
        # Коммитим все за один раз
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
    limit: int = 100,
    only_deviations: bool = False
):
    """Получить отчеты пользователя с фильтрацией по шаблону, дате и наличию отклонений"""
    query = db.query(ProcessLog).filter(ProcessLog.created_by == user_id)

    if template_id:
        query = query.filter(ProcessLog.analysis_type_id == template_id)

    if only_deviations:
        sub = db.query(IndicatorValue.process_log_id).filter(
            IndicatorValue.is_normal == False
        ).distinct()
        query = query.filter(ProcessLog.id.in_(sub))
    
    if date_from:
        query = query.filter(ProcessLog.started_at >= datetime.combine(date_from, datetime.min.time()))
    
    if date_to:
        query = query.filter(ProcessLog.started_at <= datetime.combine(date_to, datetime.max.time()))
    
    return query.order_by(ProcessLog.started_at.desc()).offset(skip).limit(limit).all()

def update_report(db: Session, report_id: int, report: ReportCreate):
    """Обновить существующий отчет"""
    db_report = db.query(ProcessLog).filter(ProcessLog.id == report_id).first()
    if not db_report:
        return None
    
    try:
        # Если передан plan_item_id, берём batch_number из PlanItem (приоритетнее frontend)
        batch_number = report.batch_number
        if report.plan_item_id:
            plan_item = db.query(PlanItem).filter(PlanItem.id == report.plan_item_id).first()
            if plan_item and plan_item.batch_number:
                batch_number = plan_item.batch_number

        db_report.batch_number = batch_number
        db_report.variety = report.variety
        db_report.container = report.container
        db_report.object_key = report.object_key

        # Удаляем старые значения показателей
        db.query(IndicatorValue).filter(IndicatorValue.process_log_id == report_id).delete()
        
        # Создаем новые значения для каждого индикатора
        for value_data in report.values:
            lib_indicator = db.query(IndicatorLibrary).filter(
                IndicatorLibrary.id == value_data.indicator_id
            ).first()
            
            if not lib_indicator:
                continue
            
            from app.services.norms import resolve_norm, variety_key_by_name
            vday = getattr(value_data, "day", None)
            norm = resolve_norm(
                db, report.template_id, value_data.indicator_id,
                day=vday, container=report.container,
                variety_key=variety_key_by_name(db, report.variety),
                object_key=report.object_key,
            )
            if norm is not None and (norm.min_value is not None or norm.max_value is not None):
                min_value, max_value = norm.min_value, norm.max_value
            else:
                template_indicator = db.query(TemplateIndicator).filter(
                    TemplateIndicator.indicator_id == value_data.indicator_id,
                    TemplateIndicator.template_id == report.template_id
                ).first()
                min_value = template_indicator.min_value if template_indicator else None
                max_value = template_indicator.max_value if template_indicator else None

            data_type = lib_indicator.data_type
            options = lib_indicator.options

            import json

            numeric_value = None
            text_value = None
            is_normal = True
            
            if data_type == 'text':
                text_value = str(value_data.value) if value_data.value is not None else None
                
            elif data_type == 'select':
                # Отклонение select — только по эталону (norm_text ниже), не по options.
                text_value = str(value_data.value) if value_data.value is not None else None

            else:
                value = value_data.value
                if isinstance(value, str):
                    try:
                        numeric_value = float(value)
                    except ValueError:
                        numeric_value = 0.0
                elif isinstance(value, (int, float)):
                    numeric_value = float(value)
                
                if numeric_value is not None and min_value is not None and max_value is not None:
                    is_normal = min_value <= numeric_value <= max_value
            
            # Нечисловая норма (список/строка): отклонение, если значение не совпало с эталоном
            if data_type in ('text', 'select') and norm is not None and getattr(norm, 'norm_text', None) and text_value:
                if str(text_value).strip().lower() != str(norm.norm_text).strip().lower():
                    is_normal = False

            db_indicator_value = IndicatorValue(
                indicator_id=value_data.indicator_id,
                value=numeric_value,
                text_value=text_value,
                day=vday,
                is_normal=is_normal,
                process_log_id=db_report.id
            )
            db.add(db_indicator_value)
        
        # Обновляем связь с планом, если передан plan_item_id
        if report.plan_item_id:
            plan_item = db.query(PlanItem).filter(PlanItem.id == report.plan_item_id).first()
            if plan_item:
                plan_item.completed_report_id = db_report.id
                plan_item.is_completed = True
                plan_item.batch_number = batch_number
        
        db.commit()
        db.refresh(db_report)
        return db_report
        
    except Exception as e:
        db.rollback()
        raise e

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