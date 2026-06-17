# WWWAnalys v3.2.0

Система для управления анализами и шаблонами показателей с библиотекой индикаторов и интеграцией с внешними системами (1С Предприятие).

## Описание

Веб-приложение для создания шаблонов анализов, управления библиотекой показателей, заполнения значений и просмотра истории отчётов. Состоит из бэкенда на FastAPI и фронтенда на React с Bootstrap 5.

### Основные возможности

- 📊 Создание и управление шаблонами анализов и пресетами
- 📚 Библиотека показателей с версионированием и категориями
- 📝 Заполнение показателей с поддержкой числовых, текстовых и select типов
- 📈 Просмотр истории отчётов с фильтрацией и статистикой
- 📋 Планирование анализов и управление планами
- 👤 Аутентификация пользователей (администратор/пользователь)
- 🔗 Интеграция с 1С Предприятие для импорта справочника показателей
- 📥 Импорт/экспорт показателей (CSV, JSON, Excel)
- 🗄️ PostgreSQL / SQLite база данных
- 🐳 Docker-контейнеризация

## Структура проекта

```
wwwanalys/
├── backend/                    # Бэкенд на FastAPI
│   ├── app/
│   │   ├── api/               # API эндпоинты (11 модулей)
│   │   ├── auth/              # Аутентификация (JWT, bcrypt)
│   │   ├── core/              # Конфигурация и зависимости
│   │   ├── crud/              # CRUD операции (8 модулей)
│   │   ├── models/            # SQLAlchemy модели (11 модулей)
│   │   ├── schemas/           # Pydantic схемы (9 модулей)
│   │   └── services/          # Внешние сервисы (интеграция с 1С)
│   ├── alembic/               # Миграции Alembic
│   ├── tests/                 # Тесты
│   ├── main.py                # Точка входа
│   ├── requirements.txt       # Зависимости
│   └── .env.example           # Пример конфигурации
├── frontend/                  # Фронтенд на React
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
- **SQLAlchemy** — ORM для работы с базой данных
- **Pydantic** — валидация данных
- **PostgreSQL / SQLite** — база данных
- **JWT** — аутентификация
- **Uvicorn** — ASGI сервер
- **Alembic** — миграции базы данных
- **httpx** — HTTP клиент для интеграции с 1С

### Фронтенд
- **React 19** — UI библиотека
- **TypeScript** — статическая типизация
- **Bootstrap 5 + React-Bootstrap** — CSS фреймворк
- **React Router DOM** — маршрутизация
- **Vite** — сборщик проектов
- **Axios** — HTTP клиент

## Быстрый старт

### Требования
- Docker и Docker Compose
- Node.js 18+ (для разработки фронтенда)
- Python 3.8+ (для разработки бэкенда)

### Запуск через Docker

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd wwwanalys
```

2. Настройте окружение:
```bash
cp backend/.env.example backend/.env
# Редактируйте .env при необходимости
```

3. Запустите контейнеры:
```bash
docker-compose up -d
```

4. Проверьте работу:
- Бэкенд: http://localhost:8000
- Фронтенд: http://localhost:5173
- API документация: http://localhost:8000/docs
- PostgreSQL: localhost:5433

## API Эндпоинты

### Аутентификация
- `POST /auth/token` — Получение JWT токена
- `POST /auth/register` — Регистрация пользователя
- `GET /auth/users/me` — Текущий пользователь

### Шаблоны (Templates)
- `GET /api/templates/` — Получение всех шаблонов
- `POST /api/templates/` — Создание шаблона
- `GET /api/templates/active` — Получение активных шаблонов
- `GET /api/templates/{id}` — Получение шаблона по ID
- `PUT /api/templates/{id}` — Обновление шаблона
- `DELETE /api/templates/{id}` — Удаление шаблона
- `DELETE /api/templates/clear-all` — Очистка всех шаблонов
- `POST /api/templates/{id}/copy` — Копирование шаблона
- `POST /api/templates/from-preset` — Создание шаблона из пресета

### Библиотека показателей (Indicator Library)
- `GET /api/indicators/library` — Получение всех показателей библиотеки
- `POST /api/indicators/library` — Создание показателя библиотеки
- `PUT /api/indicators/library/{indicator_id}` — Обновление показателя библиотеки
- `DELETE /api/indicators/library/{indicator_id}` — Удаление показателя библиотеки

### Дополнительные эндпоинты библиотеки
- `GET /api/indicators/library/count` — Получение количества показателей
- `GET /api/indicators/library/{indicator_id}/versions` — Получение истории версий показателя
- `GET /api/indicators/library/check-duplicate` — Проверка дубликатов показателей
- `POST /api/indicators/library/batch/create` — Пакетное создание показателей
- `PUT /api/indicators/library/batch/update` — Пакетное обновление показателей
- `POST /api/indicators/library/batch/delete` — Пакетное удаление показателей
- `GET /api/indicators/library/export/csv` — Экспорт в CSV
- `GET /api/indicators/library/export/excel` — Экспорт в Excel
- `POST /api/indicators/library/import/csv` — Импорт из CSV
- `POST /api/indicators/library/import/json` — Импорт из JSON

### Интеграция с 1С Предприятие
- `POST /api/external/1c/test-connection` — Проверка подключения к 1С
- `POST /api/external/1c/import-indicators` — Импорт показателей из 1С
- `GET /api/external/1c/indicators` — Получение списка показателей из 1С (без сохранения)

### Пресеты (Presets)
- `GET /api/presets/` — Получение всех пресетов
- `POST /api/presets/` — Создание пресета
- `PUT /api/presets/{id}` — Обновление пресета
- `DELETE /api/presets/{id}` — Удаление пресета

### Планы анализа (Plans)
- `GET /api/plans/` — Получение всех планов
- `POST /api/plans/` — Создание плана
- `PUT /api/plans/{id}` — Обновление плана
- `DELETE /api/plans/{id}` — Удаление плана

### Отчёты (Reports)
- `GET /api/reports/` — Получение списка отчётов
- `POST /api/reports/` — Создание отчёта
- `GET /api/reports/{id}` — Получение детальной информации об отчёте
- `GET /api/reports/filtered/list` — Отчёты с фильтрацией
- `DELETE /api/reports/history/clear` — Очистка истории

### Статистика
- `GET /api/statistics/` — Получение статистики по отчётам

### Логирование процессов
- `GET /api/process-log/` — Получение логов процессов
- `POST /api/process-log/` — Создание записи лога

## Модели данных

### Пользователь (User)
- id: int
- username: str
- email: str
- is_admin: bool
- is_active: bool
- hashed_password: str

### Библиотека показателей (IndicatorLibrary)
- id: int
- name: str
- description: str
- category: str
- created_by: int
- created_at: datetime

### Версия библиотеки (IndicatorLibraryVersion)
- id: int
- library_id: int
- version: int
- created_at: datetime
- created_by: int

### Показатель (Indicator)
- id: int
- library_id: int
- name: str
- unit: str
- data_type: str ('number', 'text', 'select')
- options: str (JSON для select)
- description: str
- category: str
- is_required: bool
- default_value: str
- validation_rules: str (JSON)
- created_by: int
- created_at: datetime

### Значение показателя (IndicatorValue)
- id: int
- indicator_id: int
- value: float | null
- text_value: str | null
- is_normal: bool
- process_log_id: int

### Тип анализа (AnalysisType)
- id: int
- name: str
- description: str
- created_by: int
- is_active: bool
- template_indicators: List[TemplateIndicator]

### Показатель шаблона (TemplateIndicator)
- id: int
- template_id: int
- indicator_id: int (ссылка на Indicator)
- min_value: float | null
- max_value: float | null
- sort_order: int
- is_custom: bool
- template_notes: str

### Пресет (Preset)
- id: int
- name: str
- description: str
- category: str
- created_by: int

### План анализа (AnalysisPlan)
- id: int
- name: str
- description: str
- analysis_type_id: int
- created_by: int
- status: str

### Процесс лог (ProcessLog)
- id: int
- batch_number: str
- analysis_type_id: int
- created_by: int
- status: str ('pending', 'completed', 'failed')
- started_at: datetime
- notes: str | null

## Интеграция с 1С Предприятие

Система поддерживает импорт справочника показателей из 1С Предприятие через REST API.

### Настройка подключения

1. Убедитесь, что 1С Предприятие настроено на публикацию REST API (через HTTP-сервисы)
2. В админ-панели перейдите на вкладку "Справочник показателей"
3. Нажмите кнопку "Загрузить из 1С"
4. Укажите параметры подключения:
   - URL сервера 1С
   - API-ключ (если используется)
   - Логин и пароль (если используется Basic Auth)

### Маппинг полей

При импорте можно настроить соответствие полей между 1С и локальной системой:
```json
{
  "name": "Наименование",
  "unit": "ЕдиницаИзмерения",
  "data_type": "ТипДанных",
  "description": "Описание",
  "category": "Категория"
}
```

### API для интеграции

```bash
# Проверка подключения
curl -X POST http://localhost:8000/api/external/1c/test-connection \
  -H "X-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"connection": {"base_url": "http://1c-server:8080", "api_key": "your-key"}}'

# Импорт показателей
curl -X POST http://localhost:8000/api/external/1c/import-indicators \
  -H "X-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "connection": {"base_url": "http://1c-server:8080"},
    "field_mapping": {
      "name": "Наименование",
      "unit": "ЕдиницаИзмерения"
    }
  }'
```

## Роли пользователей

### Администратор
- Доступ ко всем шаблонам
- Управление пользователями
- Управление справочником показателей
- Импорт/экспорт показателей
- Интеграция с внешними системами
- Полный доступ к отчётам

### Пользователь
- Доступ к активным шаблонам
- Создание отчётов
- Просмотр истории своих отчётов

## Разработка

### Добавление нового API эндпоинта
1. Создайте схему в `app/schemas/`
2. Реализуйте CRUD операции в `app/crud/`
3. Добавьте эндпоинт в `app/api/`
4. Обновите фронтенд в `frontend/src/`

### Изменение моделей
1. Измените SQLAlchemy модель в `app/models/`
2. Обновите Pydantic схему в `app/schemas/`
3. Примените миграции (если используется Alembic)

### Фронтенд разработка
- Компоненты находятся в `frontend/src/components/`
- Страницы в `frontend/src/pages/`
- Типы в `frontend/src/types/`
- API запросы в `frontend/src/api/`

## Тестирование

### API тесты
```bash
cd backend
pytest
```

### Интеграционные тесты
```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## Деплой

### Docker
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Ручной деплой
1. Соберите образы:
```bash
docker build -t wwwanalys-backend ./backend
docker build -t wwwanalys-frontend ./frontend
```

2. Запустите контейнеры с продакшн конфигурацией

## Версии

- **v1.0.0** — Initial release with admin panel and analysis constructor
- **v2.0.0** — Save current version
- **v3.0.0** — Full fix for reports and templates with UI improvements
- **v3.0.0-bootstrap** — feat: migrate frontend from Tailwind CSS to Bootstrap 5
- **v3.1.0** — feat: add indicator library with versioning and presets support
- **v3.2.0** — feat: remove template_type, remove custom indicators, add 1C integration

## Лицензия

[MIT License](LICENSE)

## Контакты

Для вопросов и предложений:
- GitHub Issues: [wwwanalys/issues](https://github.com/lunevalexsandr-web/wwwanalys/issues)

---

**WWWAnalys v3.2.0** — Система для управления анализами и шаблонами показателей с интеграцией 1С