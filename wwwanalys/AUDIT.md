# Аудит проекта WWWAnalys

**Дата:** 14.07.2026 (обновлено)
**Версия проекта:** 6.7.0

---

## 1. Общая информация

**WWWAnalys** — веб-приложение для сбора, анализа и хранения данных различных показателей с библиотекой индикаторов, шаблонами анализа, планами и двусторонней интеграцией с внешними системами (1С Предприятие).

| Компонент | Технологии |
|-----------|------------|
| **Backend** | FastAPI, SQLAlchemy 2.0, Pydantic v2, python-jose (JWT), Passlib (bcrypt) |
| **Frontend** | React 19, TypeScript, чистый CSS (SaaS-стиль, без Bootstrap Icons), React Router v7, Vite |
| **База данных** | SQLite (dev) / PostgreSQL (prod) |
| **Аутентификация** | JWT-токены, Bearer-схема |
| **Деплой** | Docker Compose |

---

## 2. Структура проекта

```
wwwanalys/
├── docker-compose.yml           # Оркестрация контейнеров
├── AUDIT.md                     # Настоящий отчет
├── PROJECT_STRUCTURE.md         # Описание структуры
├── README.md                    # Основная документация
├── backend/
│   ├── .env.example             # Пример переменных окружения
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                  # Точка входа FastAPI
│   ├── seed.py                  # Сид-данные
│   ├── alembic/                 # Миграции Alembic
│   ├── tests/                   # Тесты
│   └── app/
│       ├── core/                # config.py, database.py, deps.py
│       ├── models/              # 13 моделей (вкл. PresetIndicator, PlanItem)
│       ├── schemas/             # Pydantic схемы
│       ├── crud/                # CRUD операции
│       ├── api/                 # 10 роутеров
│       ├── auth/                # auth.py (JWT + bcrypt)
│       └── services/            # external_integration.py (1С)
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx, App.tsx, App.css, index.css
│       ├── components/          # 10+ компонентов
│       ├── pages/               # Login, Dashboard, Admin, Plans
│       ├── context/             # AuthContext.tsx
│       ├── hooks/               # useToast.ts
│       ├── types/               # index.ts
│       └── api/                 # axios.ts
├── docs/
│   └── API.md
└── README.md
```

### API роутеры (`backend/app/api/`)
| Файл | Префикс | Назначение |
|------|---------|------------|
| `auth.py` | `/auth` | Аутентификация (JWT, регистрация, me) |
| `indicators.py` | `/api/indicators` | Библиотека показателей + импорт/экспорт |
| `templates.py` | `/api/templates` | Шаблоны анализа (admin) |
| `reports.py` | `/api/reports` | Отчёты |
| `analysis_type.py` | `/analysis-types` | Legacy-алиас шаблонов |
| `presets.py` | `/api/presets` | Пресеты |
| `plans.py` | `/api/plans` | Планы анализа |
| `statistics.py` | `/api/statistics` | Статистика |
| `process_log.py` | `/process-logs` | Логирование процессов |
| `external.py` | `/api/external` | Интеграция с 1С (импорт/экспорт/синхронизация) |

---

## 3. 🔴 КРИТИЧЕСКИЕ ПРОБЛЕМЫ

### 3.1 Безопасность ✅

| № | Файл | Проблема | Статус | Исправление |
|---|------|----------|--------|-------------|
| 1 | `config.py` | Хардкодный `SECRET_KEY` | ✅ Исправлено | Читается из env |
| 2 | `external.py` | Хардкодный `API_KEY` | ✅ Исправлено | Читается из `settings.api_key`, заголовок `X-API-KEY` |
| 3 | `main.py` | CORS открыт всем | ✅ Исправлено | `settings.cors_origins_list` |
| 4 | `auth.py` | `sha256_crypt` вместо `bcrypt` | ✅ Исправлено | `schemes=["bcrypt"]` |

### 3.2 Дублирование API-роутов ⚠️

| Префикс | Файл | Статус |
|---------|------|--------|
| `/api/templates/` | `templates.py` | Admin (основной) |
| `/analysis-types/` | `analysis_type.py` | Legacy-алиас, дублирует функциональность |

Рекомендуется объединить `/analysis-types/` с `/api/templates/` или сделать редирект.

---

## 4. 🟡 СРЕДНИЕ ПРОБЛЕМЫ

| № | Проблема | Статус |
|---|----------|--------|
| 1 | Alembic не настроен (таблицы создаются через `Base.metadata.create_all`) | ⚠️ Требует инициализации |
| 2 | Нет версионирования API (`/v1/`) | ⚠️ Не реализовано |
| 3 | Порядок маршрутов в reports.py | ✅ Исправлено |
| 4 | Двусторонняя интеграция с 1С расширена, но не покрыта тестами | ⚠️ |

---

## 5. 🟢 ЗЕЛЁНАЯ ЗОНА (сделано хорошо)

| Аспект | Оценка |
|--------|--------|
| **Архитектура** | ✅ Отлично — слоистая (API, CRUD, Models, Schemas, Services) |
| **Модели данных** | ✅ Отлично — 13 сущностей с корректными связями (вкл. PresetIndicator, PlanItem) |
| **Frontend UI** | ✅ Отлично — SaaS-редизайн, чистый CSS, без Bootstrap Icons (с v6.6.0) |
| **Аутентификация** | ✅ Отлично — JWT + bcrypt, интерцепторы axios |
| **Типизация** | ✅ Хорошо — TypeScript (frontend), Pydantic v2 (backend) |
| **Локализация** | ✅ Отлично — интерфейс на русском |
| **CRUD-операции** | ✅ Хорошо — полный CRUD + batch операции |
| **Docker** | ✅ Хорошо — docker-compose с профилями |
| **AuthModal** | ✅ Новое — SaaS-стиль, CSS-переменные, адаптивность, dark mode |
| **Интеграция 1С** | ✅ Расширена — импорт показателей/шаблонов/планов + экспорт отчётов/планов |

---

## 6. 📋 РЕКОМЕНDAЦИИ

### Приоритет 2 (среднесрочно)
- [ ] Удалить или задепрекейтить дублирующийся роут `/analysis-types/`
- [ ] Настроить Alembic для автоматических миграций
- [ ] Добавить версионирование API (`/v1/`)
- [ ] Покрыть интеграцию с 1С тестами

### Приоритет 3 (долгосрочно)
- [ ] Ограничить CORS конкретными доменами в production
- [ ] Добавить rate limiting на эндпоинты auth и external
- [ ] Добавить логирование действий пользователей (audit trail)
- [ ] Покрыть тестами все API-эндпоинты
- [ ] Добавить CI/CD (GitHub Actions) для проверки линтеров и тестов

---

## 7. 🐳 Переменные окружения

### `backend/.env`
```env
DATABASE_URL=sqlite:///./test.db
SECRET_KEY=<сгенерировать: python -c "import secrets; print(secrets.token_urlsafe(32))">
API_KEY=<сгенерировать: python -c "import secrets; print(secrets.token_urlsafe(16))">
CORS_ORIGINS=http://localhost:5173,http://localhost:80
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Запуск сида
```bash
docker compose --profile seed run seed
```

---

## 8. 📊 Модель данных (ER-диаграмма)

```
┌──────────────┐       ┌────────────────────┐       ┌────────────────────┐
│     User     │       │  IndicatorLibrary  │       │ IndicatorLibrary   │
├──────────────┤       ├────────────────────┤       │      Version       │
│ id           │──┐    │ id                 │──┐    ├────────────────────┤
│ username     │  │    │ name               │  │    │ id                 │
│ email        │  │    │ description        │  │    │ library_id         │──┘
│ hashed_pwd   │  │    │ category           │  │    │ version            │
│ is_active    │  │    │ data_type          │  │    │ created_at         │
│ is_admin     │  └──┐ │ options            │  │    │ created_by         │
└──────────────┘     │ └────────────────────┘  │    └────────────────────┘
                      │                         │
┌──────────────┐     │ ┌────────────────────┐  │    ┌────────────────────┐
│  Indicator   │     │ │      Indicator     │  │    │   AnalysisType     │
├──────────────┤     │ ├────────────────────┤  │    ├────────────────────┤
│ id           │     │ │ id                 │  │    │ id                 │
│ library_id   │─────┘ │ library_id         │──┘    │ name               │
│ name         │       │ name               │       │ description        │
│ unit         │       │ data_type          │       │ created_by         │──┐
│ data_type    │       │ options            │       │ is_active          │  │
│ options      │       │ description        │       │ created_at         │  │
│ description  │       │ category           │       └────────────────────┘  │
│ category     │       │ is_required        │       ┌────────────────────┐  │
│ is_required  │       │ default_value      │       │  TemplateIndicator │  │
│ default_value│       │ validation_rules   │       ├────────────────────┤  │
│ validation   │       │ created_by         │       │ id                 │  │
│ created_by   │       │ created_at         │       │ template_id        │──┘
│ created_at   │       └────────────────────┘       │ indicator_id       │──┐
└──────────────┘                                     │ min_value          │  │
         │                        │                  │ max_value          │  │
         │                        │                  │ sort_order         │  │
         │                        │                  │ is_custom          │  │
         │                        │                  │ template_notes     │  │
         │                        │                  └────────────────────┘  │
         │                        │                                          │
         │  ┌────────────────────┐│  ┌────────────────────┐  ┌──────────────┐
         │  │  IndicatorValue    ││  │    ProcessLog      │  │ AnalysisPlan │
         │  ├────────────────────┤│  ├────────────────────┤  ├──────────────┤
         │  │ id                 ││  │ id                 │  │ id           │
         │  │ indicator_id       │┘  │ batch_number       │  │ name         │
         │  │ process_log_id     │───┤ analysis_type_id   │──┤ description  │
         │  │ value (float)      │   │ created_by         │──┤ analysis_type│
         │  │ text_value         │   │ status             │  │ created_by   │
         │  │ is_normal          │   │ started_at         │  │ status       │
         │  └────────────────────┘   │ completed_at       │  │ plan_date    │
         │                           │ notes              │  └──────────────┘
         │                           └────────────────────┘         │
         │                                                     ┌─────┴─────────┐
         │                                                     │   PlanItem    │
         │                                                     ├───────────────┤
         │                                                     │ id            │
         │                                                     │ plan_id       │
         │                                                     │ template_id   │
         │                                                     │ batch_number  │
         │                                                     │ sort_order    │
         │                                                     └───────────────┘
         │
         │   ┌────────────────────┐
         └──►│      Preset        │       ┌────────────────────┐
             ├────────────────────┤       │   PresetIndicator  │
             │ id                 │──┐    ├────────────────────┤
             │ name               │  │    │ id                 │
             │ description        │  │    │ preset_id          │
             │ category           │  │    │ indicator_id       │
             │ created_by         │  │    │ min_value          │
             └────────────────────┘  │    │ max_value          │
                                     └───►│ sort_order         │
                                          └────────────────────┘
```

---

## 9. История изменений

| Версия | Дата | Что сделано |
|--------|------|-------------|
| v1.0.0 | — | Initial release with admin panel and analysis constructor |
| v3.0.0 | — | Full fix for reports and templates with UI improvements |
| v3.0.0-bootstrap | — | Migrate frontend from Tailwind CSS to Bootstrap 5 |
| v3.1.0 | — | Add indicator library with versioning and presets support |
| v3.2.0 | 02.06.2026 | Remove template_type, custom indicators, add 1C integration |
| v3.2.0 | 17.06.2026 | Add AuthModal component (SaaS-style), add Plans page |
| v4.0.0 | — | Крупное обновление архитектуры |
| v5.0.0 | — | Расширение функциональности |
| v6.0.0 | — | Переработка планов и отчётов (передача batch_number) |
| v6.4.0 | — | Add AuthModal SaaS-style component |
| v6.5.0 | — | Modern SaaS redesign of all frontend pages |
| v6.6.0 | — | Полное удаление Bootstrap Icons, переход на чистый CSS |
| v6.7.0 | 14.07.2026 | Расширенная интеграция с 1С: справочники, шаблоны, планы (двусторонний обмен) |

---

*Отчёт создан: 02.06.2026, последнее обновление: 14.07.2026 (v6.7.0)*