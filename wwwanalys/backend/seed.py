import sys
import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models import User, AnalysisType, Indicator
from app.auth.auth import get_password_hash
from app.core.config import settings

def create_admin_user(db: Session):
    # Проверяем, существует ли уже admin пользователь
    admin_user = db.query(User).filter(User.email == "admin@brewery.com").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@brewery.com",
            hashed_password=get_password_hash("adm"),
            is_active=True,
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print("Admin пользователь создан")
    else:
        print("Admin пользователь уже существует")

def create_regular_user(db: Session):
    # Проверяем, существует ли уже regular пользователь
    regular_user = db.query(User).filter(User.email == "lab@brewery.com").first()
    if not regular_user:
        regular_user = User(
            username="lab",
            email="lab@brewery.com",
            hashed_password=get_password_hash("lab"),
            is_active=True,
            is_admin=False
        )
        db.add(regular_user)
        db.commit()
        db.refresh(regular_user)
        print("Regular пользователь создан")
    else:
        print("Regular пользователь уже существует")

def create_analysis_template(db: Session):
    # Проверяем, существует ли шаблон "Варка сусла"
    existing_template = db.query(AnalysisType).filter(AnalysisType.name == "Варка сусла").first()
    if not existing_template:
        # Создаем шаблон
        template = AnalysisType(
            name="Варка сусла",
            description="Шаблон для анализа процесса варки сусла",
            created_by=1  # ID пользователя, созданного первым (admin)
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        
        # Создаем индикаторы
        indicators = [
            Indicator(
                name="Экстрактивность",
                unit="%",
                min_value=11.0,
                max_value=12.0,
                analysis_type_id=template.id
            ),
            Indicator(
                name="Кислотность",
                unit="pH",
                min_value=5.2,
                max_value=5.8,
                analysis_type_id=template.id
            )
        ]
        
        for indicator in indicators:
            db.add(indicator)
        
        db.commit()
        print("Шаблон 'Варка сусла' с индикаторами создан")
    else:
        print("Шаблон 'Варка сусла' уже существует")

def main():
    # Создаем таблицы, если их нет
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Начало сиддинга...")
        
        # Создаем пользователей
        create_admin_user(db)
        create_regular_user(db)
        
        # Создаем шаблон анализа
        create_analysis_template(db)
        
        print("Сиддинг завершен успешно!")
    except Exception as e:
        print(f"Ошибка при сиддинге: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()