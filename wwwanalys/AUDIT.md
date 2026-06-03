# Аудит проекта WWWAnalys

**Дата:** 02.06.2026 (обновлено)
**Версия проекта:** 1.0.0

---

## 1. Общая информация

**WWWAnalys** — веб-приложение для учета производственных анализов (пивоварение).

| Компонент | Технологии |
|-----------|------------|
| **Backend** | FastAPI, SQLAlchemy 2.0, Python-JOSE, Passlib, Pydantic |
| **Frontend** | React 18, TypeScript, React-Bootstrap, Vite |
| **База данных** | SQLite (dev) / PostgreSQL 15 (prod) |
| **Аутентификация** | JWT-токены, Bearer-схема |
| **Деплой** | Docker Compose (4 сервиса: db, backend, seed, frontend) |

---

## 2. Структура проекта

> **Примечание:** В корне репозитория находился старый неиспользуемый `backend/` (пустой alembic) и `docker-compose.yml` от другого проекта (`brewery`). Они удалены. Весь код — в директории `wwwanalys/`.

```
wwwanalys/
├── docker-compose.yml          # Оркестрация контейнеров
├── AUDIT.md                    # Настоящий отчет
├── backend/
│   ├── .dockerignore           # 🆕 Исключения для Docker-образа
│   ├── .env.example            # 🆕 Пример переменных окружения
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # Точка входа FastAPI
│   ├── seed.py                 # Сид-данные (только ручной запуск)
│   ├── test_api.py
│   ├── test.db                 # SQLite для локальной разработки
│   ├── alembic/                # Миграции (не настроены)
│   │   └── versions/           # Пусто
│   └── app/
│       ├── core/
│       │   ├── config.py       # ✅ Читает SECRET_KEY, API_KEY из env
│       │   ├── database.py
│       │   └── deps.py         # ✅ Единый get_db()
│       ├── models/
│       │   ├── user.py
│       │   ├── analysis_type.py
│       │   ├── indicator.py
│       │   ├── process_log.py
│       │   └── indicator_value.py
│       ├── schemas/
│       │   ├── report.py       # ✅ Report.values теперь IndicatorValueReport
│       │   ├── ...
│       ├── crud/
│       │   └── ...
│       ├── api/
│       │   ├── auth.py
│       │   ├── templates.py
│       │   ├── reports.py      # ✅ Статические маршруты до динамических
│       │   ├── analysis_type.py # ✅ Использует deps.get_db()
│       │   ├── process_log.py   # ✅ Использует deps.get_db()
│       │   └── external.py     # ✅ API_KEY из config, использует deps.get_db()
│       └── auth/
│           └── auth.py         # ✅ bcrypt вместо sha256_crypt
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    └── src/
        ├── App.tsx
        ├── pages/
        │   ├── Dashboard.tsx   # ✅ setTimeout для сброса фильтра
        │   ├── Admin.tsx
        │   └── Login.tsx
        └── ...
```

---

## 3. 🔴 ИСПРАВЛЕННЫЕ КРИТИЧЕСКИЕ ПРОБЛЕМЫ

### 3.1 Безопасность ✅

| № | Файл | Проблема | Статус | Исправление |
|---|------|----------|--------|-------------|
| 1 | `config.py` | Хардкодный `SECRET_KEY` | ✅ Исправлено | Читается из env, в .env.example шаблон |
| 2 | `external.py` | Хардкодный `API_KEY` | ✅ Исправлено | Читается из `settings.api_key` |
| 3 | `main.py` | CORS открыт всем `["*"]` | ✅ Исправлено | Читается из `settings.cors_origins_list` |
| 4 | `auth.py` | `sha256_crypt` вместо `bcrypt` | ✅ Исправлено | `schemes=["bcrypt"]` |

### 3.2 Дублирование `get_db()` ✅

| Файл | Статус |
|------|--------|
| `api/analysis_type.py` | ✅ Исправлено — использует `from app.core.deps import get_db` |
| `api/process_log.py` | ✅ Исправлено — использует `from app.core.deps import get_db` |
| `api/external.py` | ✅ Исправлено — использует `from app.core.deps import get_db` |

### 3.3 Дублирование API-роутов ⚠️ НЕ ИСПРАВЛЕНО

| Префикс | Файл | Статус |
|---------|------|--------|
| `/api/templates/` | `templates.py` | Admin |
| `/analysis-types/` | `analysis_type.py` | Authenticated + Admin |

Рекомендуется удалить `/analysis-types/` или сделать его редиректом.

### 3.4 Несоответствие схем ✅

| Файл | Проблема | Статус |
|------|----------|--------|
| `schemas/report.py` | `values: List[IndicatorSchema]` → `IndicatorValueReport` | ✅ Исправлено |
| `schemas/report.py` | `from_orm_with_alias` возвращал пустой `values` | ✅ Исправлено — наполняется из `obj.indicator_values` |

### 3.5 Docker-деплой ✅

| № | Проблема | Статус |
|---|----------|--------|
| 1 | Отсутствует `.dockerignore` | ✅ Добавлен `backend/.dockerignore` |
| 2 | Volume перетирает pip-пакеты | ⚠️ Осталось — volume оставлен для hot-reload |
| 3 | seed.py при каждом запуске | ✅ Вынесен в отдельный сервис `seed` с профилем |
| 4 | `DATABASE_URL` не читается | ✅ Исправлено — config.py читает `DATABASE_URL` из env |

---

## 4. 🟡 ИСПРАВЛЕННЫЕ СРЕДНИЕ ПРОБЛЕМЫ

| № | Проблема | Статус |
|---|----------|--------|
| 1 | Alembic не настроен | ⚠️ НЕ ИСПРАВЛЕНО — требует инициализации |
| 2 | Нет версионирования API | ⚠️ НЕ ИСПРАВЛЕНО |
| 3 | `null` в URL при сбросе фильтра | ✅ Исправлено — `setTimeout(fetchReports, 0)` |
| 4 | Порядок маршрутов в reports.py | ✅ Исправлено — статические маршруты до `/{report_id}` |

---

## 5. 🟢 ЗЕЛЕНАЯ ЗОНА (сделано хорошо)

| Аспект | Оценка |
|--------|--------|
| **Архитектура** | ✅ Отлично |
| **Модели данных** | ✅ Отлично |
| **Frontend UI** | ✅ Отлично |
| **Seed data** | ✅ Хорошо |
| **Типизация** | ✅ Хорошо |
| **Локализация** | ✅ Отлично |
| **Аутентификация** | ✅ Хорошо |
| **CRUD-операции** | ✅ Хорошо |
| **Фильтрация отчетов** | ✅ Хорошо |
| **Docker Compose** | ✅ Хорошо (после исправлений) |

---

## 6. 📋 ОСТАВШИЕСЯ РЕКОМЕНДАЦИИ

### Приоритет 2 (среднесрочно)
- [ ] Удалить или задепрекейтить дублирующийся роут `/analysis-types/`
- [ ] Настроить чтение `DATABASE_URL` из переменных окружения в `config.py` ✅

### Приоритет 3 (долгосрочно)
- [ ] Настроить Alembic для миграций схемы БД
- [ ] Добавить версионирование API (`/v1/`)
- [ ] Ограничить CORS конкретными доменами

---

## 7. 🐳 Переменные окружения

### `backend/.env`
```env
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=<сгенерировать: python -c "import secrets; print(secrets.token_urlsafe(32))">
API_KEY=<сгенерировать: python -c "import secrets; print(secrets.token_urlsafe(16))">
CORS_ORIGINS=http://localhost:5173
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Запуск сида
```bash
docker compose --profile seed run seed
```

---

## 8. 📊 Модель данных (ER-диаграмма)

```
┌──────────────┐       ┌────────────────┐       ┌────────────────┐
│     User     │       │  AnalysisType  │       │   ProcessLog   │
├──────────────┤       ├────────────────┤       ├────────────────┤
│ id           │──┐    │ id             │──┐    │ id             │
│ username     │  │    │ name           │  │    │ batch_number   │
│ email        │  │    │ description    │  │    │ analysis_type_id│─┘
│ hashed_pwd   │  │    │ created_by     │──┤    │ created_by     │──┐
│ is_active    │  │    │ is_active      │  │    │ status         │  │
│ is_admin     │  └──┐ │ created_at     │  │    │ started_at     │  │
└──────────────┘      │ └────────────────┘  │    │ completed_at    │  │
                      │                    │    │ notes           │  │
┌──────────────┐      │ ┌────────────────┐  │    └────────────────┘  │
│  Indicator   │      │ │ IndicatorValue │  │                        │
├──────────────┤      │ ├────────────────┤  │                        │
│ id           │      │ │ id             │  │                        │
│ name         │      │ │ indicator_id   │──┘                        │
│ unit         │      │ │ process_log_id │──┘                        │
│ min_value    │      │ │ value (float)  │                           │
│ max_value    │      │ │ text_value     │                           │
│ data_type    │      │ │ is_normal      │                           │
│ options      │      │ │ measured_at    │                           │
│ analysis_type_id│───┘  │ notes          │                           │
└──────────────┘       └────────────────┘                           │
                                                                    │
                    ┌────────────────┐                              │
                    │  Связи         │                              │
                    ├────────────────┤                              │
                    │ User → AnalysisType │                         │
                    │ User → ProcessLog   │                         │
                    │ AnalysisType → Indicator │                    │
                    │ AnalysisType → ProcessLog │                   │
                    │ ProcessLog → IndicatorValue │                │
                    │ Indicator → IndicatorValue │                  │
                    └────────────────┘                              │
```

---

## 9. Изменения в этом обновлении

| № | Файл | Что сделано |
|---|------|-------------|
| 1 | `config.py` | ✅ Добавлены `cors_origins`, `api_key`, свойство `cors_origins_list` |
| 2 | `auth.py` | ✅ `sha256_crypt` → `bcrypt` |
| 3 | `main.py` | ✅ CORS из `settings.cors_origins_list`, импорт `settings` |
| 4 | `analysis_type.py` | ✅ Удален дублирующийся `get_db()`, импорт из `deps` |
| 5 | `process_log.py` | ✅ Удален дублирующийся `get_db()`, импорт из `deps` |
| 6 | `external.py` | ✅ API_KEY из config, `get_db()` из deps |
| 7 | `report.py` (schemas) | ✅ `IndicatorValueReport` вместо `IndicatorSchema`, наполнение `values` |
| 8 | `reports.py` | ✅ Статические маршруты до динамического `/{report_id}` |
| 9 | `docker-compose.yml` | ✅ Seed вынесен в отдельный сервис с профилем, env vars |
| 10 | `.dockerignore` | 🆕 Добавлен |
| 11 | `.env.example` | 🆕 Добавлен |
| 12 | `Dashboard.tsx` | ✅ `setTimeout` для сброса фильтра |
| 13 | `AUDIT.md` | ✅ Обновлен |
| 14 | `backend/` (корень) | 🗑️ Удалён — старый пустой проект (`brewery`) |
| 15 | `docker-compose.yml` (корень) | 🗑️ Удалён — неиспользуемый, от другого проекта |

---

*Отчет создан: 02.06.2026, последнее обновление: 02.06.2026*