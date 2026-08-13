from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
from app.models import AnalysisPlan, PlanItem, IndicatorLibrary, TemplateIndicator
from app.models.analysis_type import AnalysisType
from app.schemas import AnalysisPlanCreate, AnalysisPlanUpdate, PlanItemUpdate
from datetime import date
from typing import Optional


def get_plan(db: Session, plan_id: int):
    """Получить план по ID с элементами и template_indicators."""
    return db.query(AnalysisPlan)\
        .options(
            joinedload(AnalysisPlan.plan_items)
            .joinedload(PlanItem.template)
            .joinedload(AnalysisType.template_indicators)
            .joinedload(TemplateIndicator.indicator_ref)
        )\
        .filter(AnalysisPlan.id == plan_id).first()


def get_plans(db: Session, skip: int = 0, limit: int = 100):
    """Получить все планы."""
    return db.query(AnalysisPlan)\
        .options(
            joinedload(AnalysisPlan.plan_items)
            .joinedload(PlanItem.template)
            .joinedload(AnalysisType.template_indicators)
            .joinedload(TemplateIndicator.indicator_ref)
        )\
        .offset(skip).limit(limit).all()


def get_plans_by_date(db: Session, plan_date: date):
    """Получить планы на конкретную дату."""
    from app.models import TemplateIndicator
    return db.query(AnalysisPlan)\
        .options(
            joinedload(AnalysisPlan.plan_items)
            .joinedload(PlanItem.template)
            .joinedload(AnalysisType.template_indicators)
            .joinedload(TemplateIndicator.indicator_ref)
        )\
        .filter(AnalysisPlan.plan_date == plan_date).all()


def get_plans_by_date_range(db: Session, date_from: date, date_to: date):
    """Получить планы за период."""
    return db.query(AnalysisPlan)\
        .options(
            joinedload(AnalysisPlan.plan_items)
            .joinedload(PlanItem.template)
            .joinedload(AnalysisType.template_indicators)
            .joinedload(TemplateIndicator.indicator_ref)
        )\
        .filter(AnalysisPlan.plan_date >= date_from, AnalysisPlan.plan_date <= date_to)\
        .order_by(AnalysisPlan.plan_date).all()


def create_plan(db: Session, plan: AnalysisPlanCreate, user_id: int):
    """Создать новый план анализов."""
    # Проверка на дубликат даты и имени
    existing = db.query(AnalysisPlan)\
        .filter(AnalysisPlan.plan_date == plan.plan_date, AnalysisPlan.name == plan.name)\
        .first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"План с названием '{plan.name}' на указанную дату уже существует"
        )
    
    db_plan = AnalysisPlan(
        name=plan.name,
        description=plan.description,
        plan_date=plan.plan_date,
        created_by=user_id,
        is_completed=False,
    )
    db.add(db_plan)
    db.flush()
    
    # Добавляем элементы плана
    for i, item in enumerate(plan.plan_items):
        # Проверяем, что шаблон существует
        template = db.query(AnalysisType).filter(AnalysisType.id == item.template_id).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Шаблон с ID {item.template_id} не найден"
            )
        
        plan_item = PlanItem(
            plan_id=db_plan.id,
            template_id=item.template_id,
            batch_number=item.batch_number,
            sort_order=item.sort_order or i,
            is_completed=False,
        )
        db.add(plan_item)
    
    db.commit()
    db.refresh(db_plan)
    return db_plan


def update_plan(db: Session, plan_id: int, plan: AnalysisPlanUpdate):
    """Обновить план."""
    db_plan = get_plan(db, plan_id)
    if not db_plan:
        return None
    
    if plan.name is not None:
        db_plan.name = plan.name
    if plan.description is not None:
        db_plan.description = plan.description
    if plan.plan_date is not None:
        db_plan.plan_date = plan.plan_date
    if plan.is_completed is not None:
        db_plan.is_completed = plan.is_completed

    # Синхронизация состава шаблонов (если передан). Выполненные позиции
    # (с отчётом) сохраняем, чтобы не потерять связь с отчётами.
    if plan.plan_items is not None:
        desired = {}
        for i, item in enumerate(plan.plan_items):
            desired[item.template_id] = (item, i)
        existing = {it.template_id: it for it in list(db_plan.plan_items)}
        # удаляем снятые позиции, кроме выполненных
        for it in list(db_plan.plan_items):
            if it.template_id not in desired and not it.is_completed:
                db.delete(it)
        # добавляем/обновляем
        for tid, (item, order) in desired.items():
            ex = existing.get(tid)
            if ex:
                ex.batch_number = item.batch_number
                ex.sort_order = order
            else:
                tmpl = db.query(AnalysisType).filter(AnalysisType.id == tid).first()
                if tmpl:
                    db.add(PlanItem(
                        plan_id=db_plan.id, template_id=tid,
                        batch_number=item.batch_number, sort_order=order,
                    ))

    db.commit()
    db.refresh(db_plan)
    return db_plan


def delete_plan(db: Session, plan_id: int):
    """Удалить план."""
    db_plan = get_plan(db, plan_id)
    if db_plan:
        db.delete(db_plan)
        db.commit()
    return db_plan


def update_plan_item(db: Session, item_id: int, item_update: PlanItemUpdate):
    """Обновить элемент плана (отметка выполнения)."""
    from app.schemas import PlanItemUpdate as PlanItemUpdateSchema
    
    db_item = db.query(PlanItem).filter(PlanItem.id == item_id).first()
    if not db_item:
        return None
    
    if item_update.batch_number is not None:
        db_item.batch_number = item_update.batch_number
    if item_update.is_completed is not None:
        db_item.is_completed = item_update.is_completed
    if item_update.completed_report_id is not None:
        db_item.completed_report_id = item_update.completed_report_id
    
    # Если элемент выполнен, проверяем статус всех элементов плана
    if item_update.is_completed:
        plan = db.query(AnalysisPlan).options(
            joinedload(AnalysisPlan.plan_items)
        ).filter(AnalysisPlan.id == db_item.plan_id).first()
        
        if plan and all(item.is_completed for item in plan.plan_items):
            plan.is_completed = True
    
    db.commit()
    db.refresh(db_item)
    return db_item

