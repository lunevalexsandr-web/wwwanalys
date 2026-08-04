"""Тесты для справочника показателей (IndicatorLibrary)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI
from app.core.database import Base
from app.core.deps import get_db
from app.api import auth, indicators, templates, statistics
from app.auth.auth import get_password_hash
from app.models import User, IndicatorLibrary, AnalysisType, TemplateIndicator

# Создаём тестовое приложение
app_test = FastAPI()
app_test.include_router(auth.router, prefix="/auth", tags=["auth"])
app_test.include_router(indicators.router, prefix="/api/indicators", tags=["indicators"])
app_test.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app_test.include_router(statistics.router, prefix="/api", tags=["statistics"])

# Тестовая БД
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_indicators.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app_test.dependency_overrides[get_db] = override_get_db
client = TestClient(app_test)


@pytest.fixture(autouse=True)
def setup_db():
    """Создаёт таблицы перед тестами и удаляет после."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Создаёт сессию с предустановленным админом."""
    db = TestingSessionLocal()
    
    # Создаём админа
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@test.com",
            hashed_password=get_password_hash("admin"),
            is_active=True,
            is_admin=True,
        )
        db.add(admin)
        db.commit()
    
    yield db
    
    db.close()


def get_admin_token():
    response = client.post("/auth/token", data={
        "username": "admin",
        "password": "admin",
    })
    return response.json()["access_token"]


class TestIndicatorLibrary:
    """Тесты CRUD для справочника показателей."""

    def test_create_indicator(self, db_session):
        """Создание нового показателя."""
        token = get_admin_token()
        response = client.post(
            "/api/indicators/library",
            json={
                "name": "Тестовый показатель",
                "unit": "%",
                "data_type": "number",
                "category": "quality",
                "description": "Тестовое описание",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Тестовый показатель"
        assert data["unit"] == "%"
        assert data["category"] == "quality"

    def test_create_duplicate(self, db_session):
        """Проверка на дубликат названия."""
        token = get_admin_token()
        client.post(
            "/api/indicators/library",
            json={"name": "Дубликат", "unit": "шт"},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = client.post(
            "/api/indicators/library",
            json={"name": "Дубликат", "unit": "шт"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400
        assert "уже существует" in response.text

    def test_get_indicators(self, db_session):
        """Получение списка показателей."""
        token = get_admin_token()
        # Создаём несколько
        for i in range(3):
            client.post(
                "/api/indicators/library",
                json={"name": f"Показатель {i}", "unit": "шт"},
                headers={"Authorization": f"Bearer {token}"},
            )
        response = client.get(
            "/api/indicators/library",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_search_indicators(self, db_session):
        """Поиск показателей."""
        token = get_admin_token()
        
        # Создаём показатели через API
        client.post(
            "/api/indicators/library",
            json={"name": "Кислотность", "unit": "pH", "category": "quality"},
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            "/api/indicators/library",
            json={"name": "Температура", "unit": "°C", "category": "performance"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # Поиск по названию (используем params для правильной кодировки URL)
        response = client.get(
            "/api/indicators/library",
            params={"search": "кислот"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Кислотность"

    def test_filter_by_category(self, db_session):
        """Фильтрация по категории."""
        token = get_admin_token()
        client.post(
            "/api/indicators/library",
            json={"name": "A", "unit": "шт", "category": "quality"},
            headers={"Authorization": f"Bearer {token}"},
        )
        client.post(
            "/api/indicators/library",
            json={"name": "B", "unit": "шт", "category": "safety"},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = client.get(
            "/api/indicators/library",
            params={"category": "quality"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "quality"

    def test_update_indicator(self, db_session):
        """Обновление показателя."""
        token = get_admin_token()
        created = client.post(
            "/api/indicators/library",
            json={"name": "Старое имя", "unit": "шт"},
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        
        response = client.put(
            f"/api/indicators/library/{created['id']}",
            json={"name": "Новое имя", "unit": "кг", "data_type": "number"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Новое имя"
        assert response.json()["unit"] == "кг"

    def test_delete_indicator(self, db_session):
        """Удаление показателя."""
        token = get_admin_token()
        
        # Создаём показатель через API
        created = client.post(
            "/api/indicators/library",
            json={"name": "Удаляемый", "unit": "шт"},
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        
        # Удаляем
        response = client.delete(
            f"/api/indicators/library/{created['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        
        # Проверяем, что удалён
        get_response = client.get(
            "/api/indicators/library",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert len(get_response.json()) == 0

    def test_export_csv(self, db_session):
        """Экспорт в CSV."""
        token = get_admin_token()
        
        # Создаём показатель через API
        client.post(
            "/api/indicators/library",
            json={"name": "Экспортный", "unit": "%"},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        response = client.get(
            "/api/indicators/library/export/csv",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "Экспортный" in response.text

    def test_check_duplicate(self, db_session):
        """Проверка дубликатов."""
        token = get_admin_token()
        client.post(
            "/api/indicators/library",
            json={"name": "Уникальный", "unit": "шт"},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = client.get(
            "/api/indicators/library/check-duplicate",
            params={"name": "Уникальный"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["exists"] == True


class TestTemplates:
    """Тесты для шаблонов."""

    def test_create_template(self, db_session):
        """Создание шаблона."""
        token = get_admin_token()
        
        # Сначала создаём показатель в справочнике
        ind = client.post(
            "/api/indicators/library",
            json={"name": "pH", "unit": "pH", "data_type": "number"},
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        
        # Создаём шаблон с этим показателем
        response = client.post(
            "/api/templates/",
            json={
                "name": "Тестовый шаблон",
                "description": "Описание шаблона",
                "library_indicators": [{
                    "indicator_id": ind["id"],
                    "min_value": 5.0,
                    "max_value": 8.0,
                    "sort_order": 0,
                }],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Тестовый шаблон"
        assert len(data["template_indicators"]) == 1

    def test_copy_template(self, db_session):
        """Копирование шаблона."""
        token = get_admin_token()
        
        # Создаём шаблон
        client.post(
            "/api/templates/",
            json={
                "name": "Оригинал",
                "description": "Оригинальный шаблон",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # Копируем
        templates_list = client.get(
            "/api/templates/",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        template_id = templates_list[0]["id"]
        
        response = client.post(
            f"/api/templates/{template_id}/copy",
            json={"new_name": "Копия", "new_description": "Скопированный шаблон"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Копия"


class TestStatistics:
    """Тесты статистики."""

    def test_statistics_endpoint(self, db_session):
        """Получение статистики."""
        token = get_admin_token()
        response = client.get(
            "/api/indicators/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_indicators" in data
        assert "by_category" in data
        assert "by_type" in data
        assert "most_used" in data