from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import json as json_module
from app.core.deps import get_db
from app.auth.auth import get_current_active_user, get_current_admin_user
from app.crud import indicator_library as crud
from app.models import User, IndicatorLibrary
from app.schemas.indicator_library import (
    IndicatorLibrary as IndicatorLibrarySchema,
    IndicatorLibraryCreate,
    BatchCreateRequest,
    BatchCreateResponse,
    BatchUpdateRequest,
    BatchUpdateResponse,
    BatchDeleteRequest,
    BatchDeleteResponse,
)
from app.schemas.indicator_library_version import IndicatorVersionHistory

router = APIRouter()


@router.get("/library", response_model=List[IndicatorLibrarySchema])
def get_library_indicators(
    skip: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит записей"),
    search: Optional[str] = Query(None, description="Поиск по названию, описанию и категории"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    data_type: Optional[str] = Query(None, description="Фильтр по типу данных"),
    is_required: Optional[bool] = Query(None, description="Фильтр по обязательности"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить все показатели из справочника с фильтрацией, поиском и пагинацией."""
    return crud.get_library_indicators(
        db,
        skip=skip,
        limit=limit,
        search=search,
        category=category,
        data_type=data_type,
        is_required=is_required,
    )


@router.get("/library/count")
def get_library_indicators_count(
    search: Optional[str] = Query(None, description="Поиск по названию, описанию и категории"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    data_type: Optional[str] = Query(None, description="Фильтр по типу данных"),
    is_required: Optional[bool] = Query(None, description="Фильтр по обязательности"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить количество показателей с учётом фильтров (для пагинации)."""
    count = crud.get_library_indicators_count(
        db,
        search=search,
        category=category,
        data_type=data_type,
        is_required=is_required,
    )
    return {"count": count}


@router.post("/library", response_model=IndicatorLibrarySchema)
def create_library_indicator(
    indicator: IndicatorLibraryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Создать новый показатель в справочнике (только админ)."""
    existing = crud.get_library_indicator_by_name(db, indicator.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Показатель '{indicator.name}' уже существует")
    return crud.create_library_indicator(db, indicator, user_id=current_user.id)


@router.put("/library/{indicator_id}", response_model=IndicatorLibrarySchema)
def update_library_indicator(
    indicator_id: int,
    indicator: IndicatorLibraryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Обновить показатель в справочнике (только админ)."""
    db_indicator = crud.update_library_indicator(db, indicator_id, indicator, user_id=current_user.id)
    if not db_indicator:
        raise HTTPException(status_code=404, detail="Показатель не найден")
    return db_indicator


@router.delete("/library/{indicator_id}")
def delete_library_indicator(
    indicator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Удалить показатель из справочника (только админ)."""
    db_indicator = crud.delete_library_indicator(db, indicator_id, user_id=current_user.id)
    if not db_indicator:
        raise HTTPException(status_code=404, detail="Показатель не найден")
    return {"message": "Показатель успешно удален"}


# ---- Batch операции ----

@router.post("/library/batch/create", response_model=BatchCreateResponse)
def batch_create_indicators(
    request: BatchCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Создать несколько показателей за один запрос (только админ)."""
    created, errors = crud.batch_create_indicators(db, request.indicators, user_id=current_user.id)
    return BatchCreateResponse(created=created, errors=errors)


@router.put("/library/batch/update", response_model=BatchUpdateResponse)
def batch_update_indicators(
    request: BatchUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Обновить несколько показателей за один запрос (только админ)."""
    updated, errors = crud.batch_update_indicators(db, request.indicators, user_id=current_user.id)
    return BatchUpdateResponse(updated=updated, errors=errors)


@router.post("/library/batch/delete", response_model=BatchDeleteResponse)
def batch_delete_indicators(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Удалить несколько показателей за один запрос (только админ)."""
    deleted_ids, errors = crud.batch_delete_indicators(db, request.ids, user_id=current_user.id)
    return BatchDeleteResponse(deleted_ids=deleted_ids, errors=errors)


# ---- API для истории версий ----

@router.get("/library/{indicator_id}/versions", response_model=List[IndicatorVersionHistory])
def get_indicator_versions(
    indicator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить историю изменений показателя."""
    from app.crud.indicator_library_version import get_versions_for_indicator
    versions = get_versions_for_indicator(db, indicator_id)
    return versions


# ---- Связанные показатели и рекомендации ----

@router.get("/library/{indicator_id}/related")
def get_related_indicators(
    indicator_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получить связанные показатели (из той же категории)."""
    indicator = crud.get_library_indicator(db, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="Показатель не найден")
    
    related = crud.get_library_indicators(
        db,
        category=indicator.category,
        limit=limit + 1,  # +1 так как сам себя исключим
    )
    # Исключаем сам indicator
    related = [r for r in related if r.id != indicator_id][:limit]
    return related


@router.get("/library/suggestions")
def get_indicator_suggestions(
    category: Optional[str] = Query(None, description="Категория для рекомендаций"),
    exclude_ids: str = Query("", description="ID показателей через запятую для исключения"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Рекомендовать показатели для добавления по категории."""
    exclude_list = []
    if exclude_ids:
        exclude_list = [int(x.strip()) for x in exclude_ids.split(",") if x.strip()]
    
    indicators = crud.get_library_indicators(
        db, category=category, limit=limit + len(exclude_list)
    )
    result = [ind for ind in indicators if ind.id not in exclude_list][:limit]
    return result


@router.get("/library/check-duplicate")
def check_duplicate(
    name: str = Query(..., description="Название для проверки"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Проверить, существует ли показатель с таким названием (поиск дубликатов)."""
    import difflib
    
    all_indicators = db.query(IndicatorLibrary).all()
    exact = db.query(IndicatorLibrary).filter(IndicatorLibrary.name == name).first()
    
    # Поиск похожих названий
    similar = []
    for ind in all_indicators:
        ratio = difflib.SequenceMatcher(None, name.lower(), ind.name.lower()).ratio()
        if ratio > 0.6 and ind.name != name:  # >60% совпадение
            similar.append({
                "id": ind.id,
                "name": ind.name,
                "similarity": round(ratio * 100),
            })
    similar.sort(key=lambda x: x["similarity"], reverse=True)
    similar = similar[:5]  # топ-5
    
    return {
        "exists": exact is not None,
        "existing_id": exact.id if exact else None,
        "similar": similar,
    }


# ---- Import / Export ----

@router.get("/library/export/csv")
def export_library_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Экспорт справочника показателей в CSV."""
    csv_content = crud.export_indicators_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=indicator_library.csv"
        }
    )


@router.get("/library/export/excel")
def export_library_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Экспорт справочника показателей в Excel (.xlsx)."""
    excel_bytes = crud.export_indicators_excel(db)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=indicator_library.xlsx"
        }
    )


@router.post("/library/import/csv")
def import_library_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Импорт показателей в справочник из CSV-файла."""
    if not file.filename or not (file.filename.endswith('.csv') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=400, detail="Пожалуйста, загрузите файл в формате CSV")

    content = file.file.read().decode('utf-8')
    created, errors = crud.import_indicators_csv(db, content, user_id=current_user.id)

    return {
        "message": f"Импортировано: {len(created)}, ошибок: {len(errors)}",
        "created": created,
        "errors": errors,
    }


@router.post("/library/import/json")
def import_library_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Импорт показателей в справочник из JSON-файла."""
    try:
        content = file.file.read().decode('utf-8')
        data = json_module.loads(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка парсинга JSON: {str(e)}")

    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="JSON должен быть массивом объектов")

    created = []
    errors = []

    for idx, item in enumerate(data):
        try:
            name = item.get('name', '').strip()
            if not name:
                errors.append({"row": idx + 1, "error": "Пустое название"})
                continue

            existing = crud.get_library_indicator_by_name(db, name)
            if existing:
                errors.append({"row": idx + 1, "error": f"Показатель '{name}' уже существует", "name": name})
                continue

            create_data = IndicatorLibraryCreate(
                name=name,
                unit=item.get('unit', ''),
                data_type=item.get('data_type', 'number'),
                options=item.get('options'),
                description=item.get('description'),
                category=item.get('category'),
                is_required=item.get('is_required', False),
                default_value=item.get('default_value'),
                validation_rules=item.get('validation_rules'),
            )
            db_indicator = crud.create_library_indicator(db, create_data, user_id=current_user.id)
            created.append({"id": db_indicator.id, "name": db_indicator.name})
        except Exception as e:
            errors.append({"row": idx + 1, "error": str(e), "name": item.get('name', '')})

    return {
        "message": f"Импортировано: {len(created)}, ошибок: {len(errors)}",
        "created": created,
        "errors": errors,
    }
