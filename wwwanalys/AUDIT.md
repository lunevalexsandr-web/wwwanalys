# Аудит проекта WWWAnalys

**Дата:** 17.06.2026 (обновлено)
**Версия проекта:** 3.2.0

---

## 1. Общая информация

**WWWAnalys** — веб-приложение для сбора, анализа и хранения данных различных показателей с библиотекой индикаторов, шаблонами анализа и интеграцией с внешними системами (1С Предприятие).

| Компонент | Технологии |
|-----------|------------|
| **Backend** | FastAPI, SQLAlchemy 2.0, Python-JOSE, Passlib (bcrypt), Pydantic |
| **Frontend** | React 19, TypeScript, Bootstrap 5, React-Bootstrap, Vite |
| **База данных** | SQLite (dev) / PostgreSQL (prod) |
| **Аутентификация** | JWT-токены, Bearer-схема |
| **Деплой** | Docker Compose |

---

## 2. Структура проекта

```
wwwanalys/
├── docker-compose.yml           # Оркестрация контейнеров
├── AUDIT.md                     # Настоящий отчет
├── PROJECT_STRUCTURE.md         # Детальное описание структуры
├── backend/
│   ├── .dockerignore            # Исключения для Docker-образа
│   ├── .env.example             # Пример переменных окружения
│   ├── .env                     # Файл окружения (не в Git)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                  # Точка входа FastAPI
│   ├── seed.py                  # Сид-данные (ручной запуск)
│   ├── test_api.py              # Скрипт тестирования API
│   ├── alembic/                 # Миграции Alembic
│   │   └── versions/            # Файлы версий миграций
│   ├── tests/                   # Тесты
│   │   └── test_indicators.py   # Тесты показателей
│   └── app/
│       ├── core/
│       │   ├── config.py        # Конфигурация (env vars)
│       │   ├── database.py      # Подключение к БД
│       │   └── deps.py          # Зависимости (get_db, get_current_user)
│       ├── models/              # 11 моделей данных
│       │   ├── user.py
│       │   ├── indicator_library.py
│       │   ├── indicator_library_version.py
│       │   ├── indicator.py
│       │   ├── indicator_value.py
│       │   ├── analysis_type.py
│       │   ├── template_indicator.py
│       │   ├── report.py
│       │   ├── preset.py
│       │   ├── process_log.py
│       │   └── analysis_plan.py
│       ├── schemas/             # 9 схем Pydantic
│       ├── crud/                # 8 CRUD модулей
│       ├── api/                 # 11 API эндпоинтов
│       │   ├── auth.py
│       │   ├── indicators.py
│       │   ├── templates.py
│       │   ├── reports.py
│       │   ├── analysis_type.py
│       │   ├── presets.py
│       │   ├── plans.py
│       │   ├── statistics.py
│       │   ├── process_log.py
│       │   └── external.py
│       ├── auth/
│       │   └── auth.py          # JWT + bcrypt
│       └── services/
│           └── external_integration.py  # Интеграция с 1С
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── eslint.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx             # Точка входа
│       ├── App.tsx              # Маршрутизация
│       ├── App.css
│       ├── index.css            # Глобальные стили + Bootstrap
│       ├── components/          # 11 компонентов
│       │   ├── AuthModal.tsx    # Модальное окно авторизации (SaaS)
│       │   ├── AuthModal.css    # Стили с CSS-переменными
│       │   ├── AppHeader.tsx
│       │   ├── AppToast.tsx
│       │   ├── AlertToast.tsx
│       │   ├── PageHeader.tsx
│       │   ├── ActionButtons.tsx
│       │   ├── IndicatorInput.tsx
│       │   ├── IndicatorPreview.tsx
│       │   ├── IndicatorSelector.tsx
│       │   └── TemplateBuilder.tsx
│       ├── pages/               # 4 страницы
│       │   ├── Login.tsx
│       │   ├── Dashboard.tsx
│       │   ├── Admin.tsx
│       │   └── Plans.tsx
│       ├── context/
│       │   └── AuthContext.tsx  # Контекст аутентификации
│       ├── hooks/
│       │   └── useToast.ts      # Хук уведомлений
│       ├── types/
│       │   └── index.ts         # TypeScript типы
│       └── api/
│           └── axios.ts         # HTTP клиент
├── docs/
│   └── API.md                   # Документация API
└── README.md                    # Основная документация
```

---

## 3. 🔴 КРИТИЧЕСКИЕ ПРОБЛЕМЫ

### 3.1 Безопасность ✅

| № | Файл | Проблема | Статус | Исправление |
|---|------|----------|--------|-------------|
| 1 | `config.py` | Хардкодный `SECRET_KEY` | ✅ Исправлено | Читается из env |
| 2 | `external.py` | Хардкодный `API_KEY` | ✅ Исправлено | Читается из `settings.api_key` |
| 3 | `main.py` | CORS открыт всем `["*"]` | ✅ Исправлено | Читается из `settings.cors_origins_list` |
| 4 | `auth.py` | `sha256_crypt` вместо `bcrypt` | ✅ Исправлено | `schemes=["bcrypt"]` |

### 3.2 Дублирование `get_db()` ✅

Все API-модули используют единый `get_db()` из `app.core.deps`.

### 3.3 Дублирование API-роутов ⚠️

| Префикс | Файл | Статус |
|---------|------|--------|
| `/api/templates/` | `templates.py` | Admin |
| `/analysis-types/` | `analysis_type.py` | Authenticated + Admin |

Рекомендуется удалить `/analysis-types/` или сделать его редиректом.

---

## 4. 🟡 СРЕДНИЕ ПРОБЛЕМЫ

| № | Проблема | Статус |
|---|----------|--------|
| 1 | Alembic не настроен | ⚠️ Требует инициализации |
| 2 | Нет версионирования API | ⚠️ Не реализовано |
| 3 | Порядок маршрутов в reports.py | ✅ Исправлено |

---

## 5. 🟢 ЗЕЛЁНАЯ ЗОНА (сделано хорошо)

| Аспект | Оценка |
|--------|--------|
| **Архитектура** | ✅ Отлично — разделение на слои (API, CRUD, Models, Schemas) |
| **Модели данных** | ✅ Отлично — 11 моделей с правильными связями |
| **Frontend UI** | ✅ Отлично — Bootstrap 5, компонентный подход |
| **Аутентификация** | ✅ Отлично — JWT + bcrypt |
| **Типизация** | ✅ Хорошо — TypeScript на фронтенде, Pydantic на бэкенде |
| **Локализация** | ✅ Отлично — весь интерфейс на русском |
| **CRUD-операции** | ✅ Хорошо — полный CRUD для всех сущностей |
| **Docker** | ✅ Хорошо — docker-compose с профилями |
| **AuthModal** | ✅ Новое — SaaS-стиль, CSS-переменные, адаптивность |

---

## 6. 📋 РЕКОМЕНДАЦИИ

### Приоритет 2 (среднесрочно)
- [ ] Удалить или задепрекейтить дублирующийся роут `/analysis-types/`
- [ ] Настроить Alembic для автоматических миграций
- [ ] Добавить версионирование API (`/v1/`)

### Приоритет 3 (долгосрочно)
- [ ] Ограничить CORS конкретными доменами в production
- [ ] Добавить rate limiting
- [ ] Добавить логирование действий пользователей
- [ ] Покрыть тестами все API-эндпоинты

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
┌──────────────┐       ┌────────────────────┐       ┌────────────────────┐
│     User     │       │  IndicatorLibrary  │       │ IndicatorLibrary   │
├──────────────┤       ├────────────────────┤       │      Version       │
│ id           │──┐    │ id                 │──┐    ├────────────────────┤
│ username     │  │    │ name               │  │    │ id                 │
│ email        │  │    │ description        │  │    │ library_id         │──┘
│ hashed_pwd   │  │    │ category           │  │    │ version            │
│ is_active    │  │    │ created_by         │──┤    │ created_at         │
│ is_admin     │  └──┐ │ created_at         │  │    │ created_by         │
└──────────────┘     │ └────────────────────┘  │    └────────────────────┘
                     │                         │
┌──────────────┐     │ ┌────────────────────┐  │    ┌────────────────────┐
│  Indicator   │     │ │      Indicator     │  │    │   AnalysisType     │
├──────────────┤     │ ├────────────────────┤  │    ├────────────────────┤
│ id           │     │ │ id                 │  │    │ id                 │
│ library_id   │─────┘ │ library_id         │──┘    │ name               │
│ name         │       │ name               │       │ description        │
│ unit         │       │ unit               │       │ created_by         │──┐
│ data_type    │       │ data_type          │       │ is_active          │  │
│ options      │       │ options            │       │ created_at         │  │
│ description  │       │ description        │       └────────────────────┘  │
│ category     │       │ category           │                               │
│ is_required  │       │ is_required        │       ┌────────────────────┐  │
│ default_value│       │ default_value      │       │  TemplateIndicator │  │
│ validation   │       │ validation_rules   │       ├────────────────────┤  │
│ created_by   │       │ created_by         │       │ id                 │  │
│ created_at   │       │ created_at         │       │ template_id        │──┘
└──────────────┘       └────────────────────┘       │ indicator_id       │──┐
        │                        │                  │ min_value          │  │
        │                        │                  │ max_value          │  │
        │                        │                  │ sort_order         │  │
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
        │  └────────────────────┘   │ completed_at       │  └──────────────┘
        │                           │ notes              │
        │                           └────────────────────┘
        │
        │   ┌────────────────────┐
        └──►│      Preset        │
            ├────────────────────┤
            │ id                 │
            │ name               │
            │ description        │
            │ category           │
            │ created_by         │
            └────────────────────┘
```

---

## 9. История изменений

| Версия | Дата | Что сделано |
|--------|------|-------------|
| v1.0.0 | — | Initial release with admin panel and analysis constructor |
| v2.0.0 | — | Save current version |
| v3.0.0 | — | Full fix for reports and templates with UI improvements |
| v3.0.0-bootstrap | — | Migrate frontend from Tailwind CSS to Bootstrap 5 |
| v3.1.0 | — | Add indicator library with versioning and presets support |
| v3.2.0 | 02.06.2026 | Remove template_type, remove custom indicators, add 1C integration |
| v3.2.0 | 17.06.2026 | Add AuthModal component (SaaS-style), add Plans page, update documentation |

---

*Отчёт создан: 02.06.2026, последнее обновление: 17.06.2026*