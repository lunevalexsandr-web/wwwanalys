from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
from app.models import AnalysisType, Indicator, IndicatorLibrary, TemplateIndicator
from app.schemas import AnalysisTypeCreate, AnalysisTypeUpdate
import json


def get_analysis_type(db: Session, analysis_type_id: int):
    return db.query(AnalysisType)\
        .options(joinedload(AnalysisType.indicators))\
        .options(joinedload(AnalysisType.template_indicators).joinedload(TemplateIndicator.indicator_ref))\
        .filter(AnalysisType.id == analysis_type_id).first()


def get_templates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AnalysisType)\
        .options(joinedload(AnalysisType.indicators))\
        .options(joinedload(AnalysisType.template_indicators).joinedload(TemplateIndicator.indicator_ref))\
        .offset(skip).limit(limit).all()


def get_active_templates(db: Session):
    """Получить только активные шаблоны"""
    return db.query(AnalysisType)\
        .options(joinedload(AnalysisType.indicators))\
        .options(joinedload(AnalysisType.template_indicators).joinedload(TemplateIndicator.indicator_ref))\
        .filter(AnalysisType.is_active == True).all()


def create_template(db: Session, template: AnalysisTypeCreate, user_id: int):
    """Создать новый шаблон"""
    # Проверка на дубликат имени
    existing = db.query(AnalysisType).filter(AnalysisType.name == template.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип анализа с названием '{template.name}' уже существует"
        )
    
    # Определяем тип шаблона
    template_type = template.template_type if hasattr(template, 'template_type') and template.template_type else 'hybrid'
    
    db_template = AnalysisType(
        name=template.name,
        description=template.description,
        created_by=user_id,
        is_active=True,
        template_type=template_type,
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    # Добавляем обычные индикаторы (старый подход), если они есть
    for indicator_data in template.indicators:
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
    
    # Добавляем показатели из библиотеки (новый подход)
    for lib_ref in template.library_indicators:
        # Проверяем, что показатель существует в библиотеке
        lib_indicator = db.query(IndicatorLibrary).filter(IndicatorLibrary.id == lib_ref.indicator_id).first()
        if not lib_indicator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Показатель с ID {lib_ref.indicator_id} не найден в справочнике"
            )
        
        template_indicator = TemplateIndicator(
            template_id=db_template.id,
            indicator_id=lib_ref.indicator_id,
            min_value=lib_ref.min_value,
            max_value=lib_ref.max_value,
            sort_order=lib_ref.sort_order
        )
        db.add(template_indicator)
    
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
    if template.template_type is not None and hasattr(template, 'template_type'):
        db_template.template_type = template.template_type
    
    # Если переданы обычные индикаторы, обновляем их (старый подход)
    if template.indicators is not None:
        # Удаляем старые индикаторы
        for indicator in db_template.indicators:
            db.delete(indicator)
        db.flush()
        
        # Добавляем новые индикаторы
        for indicator_data in template.indicators:
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
    
    # Если переданы показатели из библиотеки, обновляем их (новый подход)
    if template.library_indicators is not None:
        # Удаляем старые связи
        for ti in db_template.template_indicators:
            db.delete(ti)
        db.flush()
        
        # Добавляем новые связи
        for lib_ref in template.library_indicators:
            lib_indicator = db.query(IndicatorLibrary).filter(IndicatorLibrary.id == lib_ref.indicator_id).first()
            if not lib_indicator:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Показатель с ID {lib_ref.indicator_id} не найден в справочнике"
                )
            
            template_indicator = TemplateIndicator(
                template_id=db_template.id,
                indicator_id=lib_ref.indicator_id,
                min_value=lib_ref.min_value,
                max_value=lib_ref.max_value,
                sort_order=lib_ref.sort_order
            )
            db.add(template_indicator)
    
    db.commit()
    db.refresh(db_template)
    return db_template


def copy_template(db: Session, template_id: int, new_name: str, new_description: str, user_id: int):
    """Создать копию шаблона с новым именем."""
    source = get_analysis_type(db, analysis_type_id=template_id)
    if not source:
        raise HTTPException(status_code=404, detail="Шаблон для копирования не найден")
    
    # Проверка на дубликат имени
    existing = db.query(AnalysisType).filter(AnalysisType.name == new_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип анализа с названием '{new_name}' уже существует"
        )
    
    # Создаём копию
    db_template = AnalysisType(
        name=new_name,
        description=new_description or source.description,
        created_by=user_id,
        is_active=True,
        template_type=source.template_type,
    )
    db.add(db_template)
    db.flush()
    
    # Копируем обычные индикаторы
    for ind in source.indicators:
        new_ind = Indicator(
            name=ind.name,
            unit=ind.unit,
            min_value=ind.min_value,
            max_value=ind.max_value,
            data_type=ind.data_type,
            options=ind.options,
            analysis_type_id=db_template.id,
        )
        db.add(new_ind)
    
    # Копируем библиотечные индикаторы
    for ti in source.template_indicators:
        new_ti = TemplateIndicator(
            template_id=db_template.id,
            indicator_id=ti.indicator_id,
            min_value=ti.min_value,
            max_value=ti.max_value,
            sort_order=ti.sort_order,
            is_custom=ti.is_custom,
            template_notes=ti.template_notes,
        )
        db.add(new_ti)
    
    db.commit()
    db.refresh(db_template)
    return db_template


def delete_template(db: Session, template_id: int):
    db_template = get_analysis_type(db, analysis_type_id=template_id)
    if db_template:
        from app.models import IndicatorValue, ProcessLog
        
        # Удаляем значения индикаторов, связанные с индикаторами этого шаблона
        indicator_ids = [ind.id for ind in db_template.indicators]
        # Также удаляем значения для библиотечных индикаторов
        lib_indicator_ids = [ti.indicator_id for ti in db_template.template_indicators]
        all_indicator_ids = indicator_ids + lib_indicator_ids
        if all_indicator_ids:
            db.query(IndicatorValue).filter(IndicatorValue.indicator_id.in_(all_indicator_ids)).delete(synchronize_session=False)
        
        # Удаляем логи процессов, связанные с этим шаблоном
        db.query(ProcessLog).filter(ProcessLog.analysis_type_id == template_id).delete(synchronize_session=False)
        
        # TemplateIndicators удаляются каскадно (cascade="all, delete-orphan")
        
        # Удаляем индикаторы (старый подход)
        for indicator in db_template.indicators:
            db.delete(indicator)
        
        # Удаляем тип анализа
        db.delete(db_template)
        db.commit()
    return db_template


def get_indicators_by_analysis_type(db: Session, analysis_type_id: int):
    return db.query(Indicator).filter(Indicator.analysis_type_id == analysis_type_id).all()


def clear_all_templates(db: Session):
    """Удалить все шаблоны с индикаторами и значениями."""
    from app.models import IndicatorValue, ProcessLog
    
    count = db.query(AnalysisType).count()
    # Удаляем значения индикаторов (FK → indicators)
    db.query(IndicatorValue).delete()
    # Удаляем логи процессов (FK → analysis_types)
    db.query(ProcessLog).delete()
    # TemplateIndicators удаляются каскадно
    # Удаляем индикаторы (FK → analysis_types)
    db.query(Indicator).delete()
    # Удаляем шаблоны
    db.query(AnalysisType).delete()
    db.commit()
    return count


# Алиасы для совместимости с существующим кодом
def get_analysis_types(db: Session, skip: int = 0, limit: int = 100):
    return get_templates(db, skip=skip, limit=limit)


def create_analysis_type(db: Session, analysis_type: AnalysisTypeCreate, user_id: int):
    return create_template(db, analysis_type, user_id)


def update_analysis_type(db: Session, analysis_type_id: int, analysis_type: AnalysisTypeUpdate):
    return update_template(db, analysis_type_id, analysis_type)


def delete_analysis_type(db: Session, analysis_type_id: int):
    return delete_template(db, analysis_type_id)