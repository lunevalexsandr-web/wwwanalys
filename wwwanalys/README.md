# WWWAnalys v6.7.0

Система для управления анализами и шаблонами показателей с библиотекой индикаторов, планами анализа и глубокой двусторонней интеграцией с внешними системами (1С Предприятие).

## Описание

Веб-приложение для создания шаблонов анализов, управления библиотекой показателей, заполнения значений, планирования и просмотра истории отчётов. Состоит из бэкенда на FastAPI и фронтенда на React 19 с чистым CSS (SaaS-дизайн, без Bootstrap Icons).

### Основные возможности

- 📊 Создание и управление шаблонами анализов и пресетами
- 📚 Библиотека показателей с версионированием, категориями, поиском и рекомендациями
- 📝 Заполнение показателей с поддержкой числовых, текстовых и select-типов
- 📈 Просмотр истории отчётов с фильтрацией и статистикой
- 📋 Планирование анализов и управление планами (с передачей batch_number в отчёты)
- 👤 Аутентификация пользователей (администратор/пользователь) через JWT
- 🔗 Двусторонняя интеграция с 1С Предприятие: импорт справочника показателей, шаблонов и планов, а также отправка отчётов и планов обратно в 1С
- 📥 Импорт/экспорт показателей (CSV, JSON, Excel)
- 🗄️ PostgreSQL / SQLite база данных
- 🐳 Docker-контейнеризация
- 🎨 Современный SaaS-редизайн всех страниц, чистый CSS (без Bootstrap Icons)

## Структура проекта

```
wwwanalys/
├── backend/                    # Бэкенд на FastAPI
│   ├── app/
│   │   ├── api/               # API эндпоинты (10 модулей)
│   │   ├── auth/              # Аутентификация (JWT, bcrypt)
│   │   ├── core/              # Конфигурация и зависимости
│   │   ├── crud/              # CRUD операции
│   │   ├── models/            # SQLAlchemy модели (13 сущностей)
│   │   ├── schemas/           # Pydantic схемы
│   │   └── services/          # Внешние сервисы (интеграция с 1С)
│   ├── alembic/               # Миграции Alembic
│   ├── tests/                 # Тесты
│   ├── main.py                # Точка входа
│   ├── requirements.txt       # Зависимости
│   └── .env.example           # Пример конфигурации
├── frontend/                  # Фронтенд на React 19
│   ├── src/
│   │   ├── components/        # UI компоненты (AuthModal, Header, ...)
│   │   ├── pages/             # Страницы (Login, Dashboard, Admin, Plans)
│   │   ├── context/           # React контексты (AuthContext)
│   │   ├── hooks/             # Кастомные хуки (useToast)
│   │   ├── types/             # TypeScript типы
│   │   └── api/               # API клиент (axios)
│   ├── package.json           # Зависимости
│   └── vite.config.ts         # Конфигурация Vite
├── docs/                      # Документация
│   └── API.md                 # API документация
├── docker-compose.yml         # Docker Compose
└── README.md                  # Документация
```

## Технологии

### Бэкенд
- **FastAPI** — асинхронный веб-фреймворк
- **SQLAlchemy 2.0** — ORM для работы с базой данных
- **Pydantic v2** — валидация данных
- **PostgreSQL / SQLite** — база данных
- **JWT (python-jose)** — аутентификация
- **Passlib (bcrypt)** — хеширование паролей
- **Uvicorn** — ASGI сервер
- **Alembic** — миграции базы данных
- **httpx** — HTTP клиент для интеграции с 1С
- **openpyxl** — экспорт в Excel

### Фронтенд
- **React 19** — UI библиотека
- **TypeScript** — статическая типизация
- **Чистый CSS** (CSS-переменные, без Bootstrap Icons) — стилизация в SaaS-стиле
- **React Router DOM v7** — маршрутизация
- **Vite** — сборщик проектов
- **Axios** — HTTP клиент

## Быстрый старт

### Требования
- Docker и Docker Compose
- Node.js 18+ (для разработки фронтенда)
- Python 3.11+ (для разработки бэкенда)

### Запуск через Docker

1. Настройте окружение:
```bash
cp backend/.env.example backend/.env
# Отредактируйте .env при необходимости (SECRET_KEY, API_KEY, CORS_ORIGINS)
```

2. Запустите контейнеры:
```bash
docker-compose up -d
```

3. Проверьте работу:
- Бэкенд: http://localhost:8000
- Фронтенд: http://localhost:80 (или http://localhost:5173 в dev)
- API документация: http://localhost:8000/docs
- PostgreSQL: localhost:5433

### Запуск сид-данных
```bash
docker compose --profile seed run seed
```

## API Эндпоинты

### Аутентификация (`/auth`)
- `POST /auth/token` — Получение JWT токена
- `POST /auth/register` — Регистрация пользователя
- `GET /auth/users/me` — Текущий пользователь

### Шаблоны (Templates) (`/api/templates`)
- `GET /api/templates/` — Все шаблоны (admin)
- `POST /api/templates/` — Создание шаблона (admin)
- `GET /api/templates/active` — Активные шаблоны
- `GET /api/templates/{id}` — Шаблон по ID (admin)
- `PUT /api/templates/{id}` — Обновление (admin)
- `DELETE /api/templates/{id}` — Удаление (admin)
- `DELETE /api/templates/clear-all` — Очистка всех шаблонов (admin)
- `POST /api/templates/{id}/copy` — Копирование (admin)
- `POST /api/templates/from-preset` — Создание из пресета (admin)

### Библиотека показателей (Indicator Library) (`/api/indicators`)
- `GET /api/indicators/library` — Список с фильтрами, поиском и пагинацией
- `GET /api/indicators/library/count` — Количество с учётом фильтров
- `POST /api/indicators/library` — Создание (admin)
- `PUT /api/indicators/library/{id}` — Обновление (admin)
- `DELETE /api/indicators/library/{id}` — Удаление (admin)
- `POST /api/indicators/library/batch/create` — Пакетное создание (admin)
- `PUT /api/indicators/library/batch/update` — Пакетное обновление (admin)
- `POST /api/indicators/library/batch/delete` — Пакетное удаление (admin)
- `GET /api/indicators/library/{id}/versions` — История версий
- `GET /api/indicators/library/{id}/related` — Связанные показатели
- `GET /api/indicators/library/suggestions` — Рекомендации показателей
- `GET /api/indicators/library/check-duplicate` — Проверка дубликатов
- `GET /api/indicators/library/export/csv` — Экспорт в CSV
- `GET /api/indicators/library/export/excel` — Экспорт в Excel
- `POST /api/indicators/library/import/csv` — Импорт из CSV
- `POST /api/indicators/library/import/json` — Импорт из JSON

### Интеграция с 1С Предприятие (`/api/external`)
- `POST /api/external/1c/test-connection` — Проверка подключения
- `POST /api/external/1c/import-indicators` — Импорт показателей
- `GET /api/external/1c/indicators` — Получение показателей (без сохранения)
- `POST /api/external/1c/import-templates` — Импорт шаблонов
- `GET /api/external/1c/templates` — Получение шаблонов (без сохранения)
- `POST /api/external/1c/import-plans` — Импорт планов
- `GET /api/external/1c/plans` — Получение планов (без сохранения)
- `POST /api/external/1c/push-report` — Отправка отчёта в 1С
- `POST /api/external/1c/push-plan` — Отправка плана в 1С
- `POST /api/external/sync-templates` — Синхронизация шаблонов из ERP (legacy)

### Пресеты (Presets) (`/api/presets`)
- `GET /api/presets/` — Все пресеты
- `POST /api/presets/` — Создание
- `PUT /api/presets/{id}` — Обновление
- `DELETE /api/presets/{id}` — Удаление

### Планы анализа (Plans) (`/api/plans`)
- `GET /api/plans/` — Все планы
- `POST /api/plans/` — Создание
- `PUT /api/plans/{id}` — Обновление
- `DELETE /api/plans/{id}` — Удаление

### Отчёты (Reports) (`/api/reports`)
- `GET /api/reports/` — Список отчётов
- `POST /api/reports/` — Создание отчёта
- `GET /api/reports/{id}` — Детали отчёта
- `GET /api/reports/filtered/list` — Отчёты с фильтрацией
- `DELETE /api/reports/history/clear` — Очистка истории

### Статистика (`/api/statistics`)
- `GET /api/statistics/` — Статистика по отчётам

### Логирование процессов (`/process-logs`)
- `GET /process-logs/` — Логи процессов
- `POST /process-logs/` — Создание записи лога

### Типы анализа (`/analysis-types`, legacy-алиас)
- Дублирует функциональность `/api/templates` (требует унификации)

## Модели данных

### Пользователь (User)
- id, username, email, is_admin, is_active, hashed_password

### Библиотека показателей (IndicatorLibrary)
- id, name, description, category, created_by, created_at, data_type, options, is_required, default_value, validation_rules

### Версия библиотеки (IndicatorLibraryVersion)
- id, library_id, version, created_at, created_by

### Показатель (Indicator)
- id, library_id, name, unit, data_type, options, description, category, is_required, default_value, validation_rules, created_by, created_at

### Значение показателя (IndicatorValue)
- id, indicator_id, value (float|null), text_value (str|null), is_normal, process_log_id

### Тип анализа / Шаблон (AnalysisType)
- id, name, description, created_by, is_active, template_indicators[]

### Показатель шаблона (TemplateIndicator)
- id, template_id, indicator_id, min_value, max_value, sort_order, is_custom, template_notes

### Пресет (Preset)
- id, name, description, category, created_by
- PresetIndicator — связи показателей пресета

### План анализа (AnalysisPlan)
- id, name, description, analysis_type_id, created_by, status, plan_date
- PlanItem — элементы плана (template_id, batch_number, sort_order)

### Процесс лог (ProcessLog)
- id, batch_number, analysis_type_id, created_by, status, started_at, completed_at, notes

### Отчёт (Report)
- Связан с ProcessLog, содержит значения показателей и batch_number

## Интеграция с 1С Предприятие

Система поддерживает двусторонний обмен данными со 1С Предприятие через REST API (на стороне 1С публикуется HTTP-сервис).

### Импорт из 1С
- Справочник показателей (`/api/external/1c/import-indicators`)
- Шаблоны анализов (`/api/external/1c/import-templates`)
- Планы анализа (`/api/external/1c/import-plans`)

Для каждого импорта настраивается `connection` (base_url, api_key, username, password, timeout) и `field_mapping` (соответствие полей 1С → локальные).

### Экспорт в 1С
- Отправка отчёта: `POST /api/external/1c/push-report`
- Отправка плана: `POST /api/external/1c/push-plan`

### Защита
Все эндпоинты интеграции требуют заголовок `X-API-KEY`, значение сверяется с `settings.api_key`.

## Роли пользователей

### Администратор
- Доступ ко всем шаблонам и пресетам
- Управление библиотекой показателей (CRUD, импорт/экспорт, версионирование)
- Интеграция с внешними системами (1С)
- Полный доступ к отчётам и планам

### Пользователь
- Доступ к активным шаблонам
- Создание отчётов
- Просмотр истории своих отчётов
- Работа с планами анализа

## Разработка

### Структура слоёв
1. **API** (`app/api/`) — роутеры FastAPI
2. **CRUD** (`app/crud/`) — операции с БД
3. **Models** (`app/models/`) — SQLAlchemy модели
4. **Schemas** (`app/schemas/`) — Pydantic схемы
5. **Services** (`app/services/`) — внешние интеграции
6. **Core** (`app/core/`) — config, database, deps
7. **Auth** (`app/auth/`) — JWT + bcrypt

### Тестирование
```bash
cd backend
pytest
```

## Деплой

### Docker
```bash
docker-compose up -d
```

### Сборка образов
```bash
docker build -t wwwanalys-backend ./backend
docker build -t wwwanalys-frontend ./frontend
```

## Версии

- **v1.0.0** — Initial release (admin panel, конструктор анализов)
- **v2.0.0** — Сохранение состояния
- **v3.0.0** — Исправления отчётов и шаблонов, UI
- **v3.0.0-bootstrap** — Миграция на Bootstrap 5
- **v3.1.0** — Библиотека показателей с версионированием и пресетами
- **v3.2.0** — Удаление template_type/custom indicators, интеграция 1С
- **v4.0.0** — Крупное обновление архитектуры
- **v5.0.0** — Расширение функциональности
- **v6.0.0** — Переработка планов и отчётов
- **v6.1.0 – v6.3.0** — Улучшения интеграции и UI
- **v6.4.0** — AuthModal в SaaS-стиле
- **v6.5.0** — Modern SaaS redesign всех страниц
- **v6.6.0** — Полное удаление Bootstrap Icons, переход на чистый CSS
- **v6.7.0** — Расширенная интеграция с 1С: справочники, шаблоны, планы (двусторонний обмен)

## Лицензия

MIT License

## Контакты

GitHub Issues: [wwwanalys/issues](https://github.com/lunevalexsandr-web/wwwanalys/issues)

---

**WWWAnalys v6.7.0** — Система управления анализами и шаблонами показателей с двусторонней интеграцией 1С