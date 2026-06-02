from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
from app.models import AnalysisType, Indicator
from app.models.indicator import DataType
from app.schemas import AnalysisTypeCreate, AnalysisTypeUpdate
import json

def get_analysis_type(db: Session, analysis_type_id: int):
    return db.query(AnalysisType).options(joinedload(AnalysisType.indicators)).filter(AnalysisType.id == analysis_type_id).first()

def get_templates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AnalysisType).options(joinedload(AnalysisType.indicators)).offset(skip).limit(limit).all()

def get_active_templates(db: Session):
    """Получить только активные шаблоны"""
    return db.query(AnalysisType).options(joinedload(AnalysisType.indicators)).filter(AnalysisType.is_active == True).all()

def create_template(db: Session, template: AnalysisTypeCreate, user_id: int):
    """Создать новый шаблон"""
    # Проверка на дубликат имени
    existing = db.query(AnalysisType).filter(AnalysisType.name == template.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип анализа с названием '{template.name}' уже существует"
        )
    
    db_template = AnalysisType(
        name=template.name,
        description=template.description,
        created_by=user_id,
        is_active=True
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    # Добавляем индикаторы, если они есть
    for indicator_data in template.indicators:
        # Конвертируем options в JSON-строку для SELECT типа
        options_json = None
        data_type_str = indicator_data.data_type.value if hasattr(indicator_data.data_type, 'value') else str(indicator_data.data_type)
        if indicator_data.options and data_type_str == 'select':
            options_json = json.dumps(indicator_data.options)
        
        indicator = Indicator(
            name=indicator_data.name,
            unit=indicator_data.unit,
            min_value=indicator_data.min_value,
            max_value=indicator_data.max_value,
            data_type=indicator_data.data_type,
            options=options_json,
            analysis_type_id=db_template.id
        )
        db.add(indicator)
    
    db.commit()
    db.refresh(db_template)
    return db_template

def update_template(db: Session, template_id: int, template: AnalysisTypeUpdate):
    db_template = get_analysis_type(db, analysis_type_id=template_id)
    if not db_template:
        return None
    
    # Обновляем основные поля
    if template.name is not None:
        db_template.name = template.name
    if template.description is not None:
        db_template.description = template.description
    if template.is_active is not None:
        db_template.is_active = template.is_active
    
    # Если переданы индикаторы, обновляем их
    if template.indicators is not None and len(template.indicators) > 0:
        # Удаляем старые индикаторы
        for indicator in db_template.indicators:
            db.delete(indicator)
        db.flush()
        
        # Добавляем новые индикаторы
        for indicator_data in template.indicators:
            # Конвертируем options в JSON-строку для SELECT типа
            options_json = None
            data_type_str = indicator_data.data_type.value if hasattr(indicator_data.data_type, 'value') else str(indicator_data.data_type)
            if indicator_data.options and data_type_str == 'select':
                options_json = json.dumps(indicator_data.options)
            
            indicator = Indicator(
                name=indicator_data.name,
                unit=indicator_data.unit,
                min_value=indicator_data.min_value,
                max_value=indicator_data.max_value,
                data_type=indicator_data.data_type,
                options=options_json,
                analysis_type_id=db_template.id
            )
            db.add(indicator)
    
    db.commit()
    db.refresh(db_template)
    return db_template

def delete_template(db: Session, template_id: int):
    db_template = get_analysis_type(db, analysis_type_id=template_id)
    if db_template:
        # Сначала удаляем связанные индикаторы
        for indicator in db_template.indicators:
            db.delete(indicator)
        
        # Затем удаляем тип анализа
        db.delete(db_template)
        db.commit()
    return db_template

def get_indicators_by_analysis_type(db: Session, analysis_type_id: int):
    return db.query(Indicator).filter(Indicator.analysis_type_id == analysis_type_id).all()

# Алиасы для совместимости с существующим кодом
def get_analysis_types(db: Session, skip: int = 0, limit: int = 100):
    return get_templates(db, skip=skip, limit=limit)

def create_analysis_type(db: Session, analysis_type: AnalysisTypeCreate, user_id: int):
    return create_template(db, analysis_type, user_id)

def update_analysis_type(db: Session, analysis_type_id: int, analysis_type: AnalysisTypeUpdate):
    return update_template(db, analysis_type_id, analysis_type)

def delete_analysis_type(db: Session, analysis_type_id: int):
    return delete_template(db, analysis_type_id)