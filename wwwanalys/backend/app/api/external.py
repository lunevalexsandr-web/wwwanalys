from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import SessionLocal
from app.core.config import settings
from app.crud import analysis_type as crud_template
from app.schemas import AnalysisTypeCreate, AnalysisTypeUpdate
from fastapi.security import APIKeyHeader

router = APIRouter()

API_KEY = "your-secret-api-key"  # В реальном проекте хранить в env
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    return api_key

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/sync-templates")
def sync_templates(
    templates_data: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Синхронизация шаблонов из внешней ERP системы
    Защита: статичный API-ключ в Header `X-API-KEY`
    """
    try:
        for template_data in templates_data:
            # Проверяем, существует ли шаблон
            existing_template = db.query(crud_template.AnalysisType).filter(
                crud_template.AnalysisType.name == template_data["name"]
            ).first()
            
            if existing_template:
                # Обновляем существующий шаблон
                update_data = AnalysisTypeUpdate(
                    name=template_data.get("name", existing_template.name),
                    description=template_data.get("description")
                )
                crud_template.update_template(db, existing_template.id, update_data)
            else:
                # Создаем новый шаблон
                create_data = AnalysisTypeCreate(
                    name=template_data["name"],
                    description=template_data.get("description")
                )
                crud_template.create_template(db, create_data, user_id=1)  # ID системного пользователя
        
        return {"message": f"Successfully synced {len(templates_data)} templates"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")