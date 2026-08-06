"""API базы знаний технологических карт (RAG).

Загрузка/удаление — только администратор. Просмотр/поиск — любой авторизованный.
Модуль необязательный: маршрут подключается только при включённом AI_ENABLED.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.config import settings
from app.models import User
from app.models.tech_card import TechDocument
from app.auth.auth import get_current_active_user, get_current_admin_user
from app.services import rag

logger = logging.getLogger(__name__)

router = APIRouter()

_ALLOWED_EXT = (".pdf", ".docx", ".xlsx", ".txt", ".md", ".csv")


@router.post("/upload")
async def upload_tech_card(
    file: UploadFile = File(...),
    title: str = Form(""),
    variety: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Загрузить файл техкарты: распарсить, нарезать, сохранить в базу знаний."""
    fname = file.filename or "document"
    if not fname.lower().endswith(_ALLOWED_EXT):
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(_ALLOWED_EXT)}",
        )

    data = await file.read()
    max_bytes = settings.rag_max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Файл больше {settings.rag_max_upload_mb} МБ",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Пустой файл")

    try:
        doc = rag.ingest_document(
            db,
            title=title.strip() or fname,
            filename=fname,
            data=data,
            mime=file.content_type,
            variety=variety.strip() or None,
            uploaded_by=current_user.id,
        )
    except Exception as e:
        logger.exception("Ошибка загрузки техкарты %s", fname)
        raise HTTPException(status_code=422, detail=f"Не удалось обработать файл: {e}")

    return _doc_out(doc)


@router.get("")
@router.get("/")
def list_tech_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Список загруженных документов базы знаний."""
    docs = db.query(TechDocument).order_by(TechDocument.created_at.desc()).all()
    return [_doc_out(d) for d in docs]


@router.get("/search")
def search_tech_cards(
    q: str = Query(..., min_length=1),
    variety: str = Query(""),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Поиск релевантных фрагментов (для проверки/отладки базы знаний)."""
    return rag.search_chunks(db, q, variety=variety.strip() or None, limit=limit)


@router.delete("/{doc_id}")
def delete_tech_card(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Удалить документ и все его фрагменты."""
    doc = db.query(TechDocument).filter(TechDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")
    db.delete(doc)
    db.commit()
    return {"deleted": doc_id}


def _doc_out(d: TechDocument) -> dict:
    return {
        "id": d.id,
        "title": d.title,
        "variety": d.variety,
        "filename": d.filename,
        "size_bytes": d.size_bytes,
        "status": d.status,
        "char_count": d.char_count,
        "chunk_count": d.chunk_count,
        "created_at": d.created_at,
    }
