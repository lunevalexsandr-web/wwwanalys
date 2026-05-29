from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.models import AnalysisType, Indicator
from app.schemas import AnalysisTypeCreate, AnalysisTypeUpdate

def get_analysis_type(db: Session, analysis_type_id: int):
    return db.query(AnalysisType).options(joinedload(AnalysisType.indicators)).filter(AnalysisType.id == analysis_type_id).first()

def get_analysis_types(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AnalysisType).options(joinedload(AnalysisType.indicators)).offset(skip).limit(limit).all()

def create_analysis_type(db: Session, analysis_type: AnalysisTypeCreate, user_id: int):
    db_analysis_type = AnalysisType(
        name=analysis_type.name,
        description=analysis_type.description,
        created_by=user_id
    )
    db.add(db_analysis_type)
    db.commit()
    db.refresh(db_analysis_type)
    
    # Добавляем индикаторы, если они есть
    for indicator_data in analysis_type.indicators:
        indicator = Indicator(
            name=indicator_data.name,
            unit=indicator_data.unit,
            min_value=indicator_data.min_value,
            max_value=indicator_data.max_value,
            analysis_type_id=db_analysis_type.id
        )
        db.add(indicator)
    
    db.commit()
    db.refresh(db_analysis_type)
    return db_analysis_type

def update_analysis_type(db: Session, analysis_type_id: int, analysis_type: AnalysisTypeUpdate):
    db_analysis_type = get_analysis_type(db, analysis_type_id=analysis_type_id)
    if db_analysis_type:
        update_data = analysis_type.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_analysis_type, field, value)
        db.commit()
        db.refresh(db_analysis_type)
    return db_analysis_type

def delete_analysis_type(db: Session, analysis_type_id: int):
    db_analysis_type = get_analysis_type(db, analysis_type_id=analysis_type_id)
    if db_analysis_type:
        # Сначала удаляем связанные индикаторы
        for indicator in db_analysis_type.indicators:
            db.delete(indicator)
        
        # Затем удаляем тип анализа
        db.delete(db_analysis_type)
        db.commit()
    return db_analysis_type

def get_indicators_by_analysis_type(db: Session, analysis_type_id: int):
    return db.query(Indicator).filter(Indicator.analysis_type_id == analysis_type_id).all()