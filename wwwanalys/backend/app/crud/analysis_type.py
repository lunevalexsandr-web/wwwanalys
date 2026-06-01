from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
from app.models import AnalysisType, Indicator
from app.schemas import AnalysisTypeCreate, AnalysisTypeUpdate

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
        indicator = Indicator(
            name=indicator_data.name,
            unit=indicator_data.unit,
            min_value=indicator_data.min_value,
            max_value=indicator_data.max_value,
            analysis_type_id=db_template.id
        )
        db.add(indicator)
    
    db.commit()
    db.refresh(db_template)
    return db_template

def update_template(db: Session, template_id: int, template: AnalysisTypeUpdate):
    db_template = get_analysis_type(db, analysis_type_id=template_id)
    if db_template:
        update_data = template.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_template, field, value)
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