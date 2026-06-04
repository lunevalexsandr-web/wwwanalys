# WWWAnalys v3.0.0

Система для управления анализами и шаблонами показателей с библиотекой индикаторов.

## Описание

Веб-приложение для создания шаблонов анализов, управления библиотекой индикаторов, заполнения показателей и просмотра истории отчётов. Состоит из бэкенда на FastAPI и фронтенда на React с Bootstrap 5.

### Основные возможности

- 📊 Создание и управление шаблонами анализов и пресетами
- 📚 Библиотека индикаторов с версионированием
- 📝 Заполнение показателей с поддержкой числовых, текстовых и select типов
- 📈 Просмотр истории отчётов с фильтрацией и статистикой
- 👤 Аутентификация пользователей (администратор/пользователь)
- 🗄️ PostgreSQL база данных
- 🐳 Docker-контейнеризация

## Структура проекта

```
wwwanalys/
├── backend/                 # Бэкенд на FastAPI
│   ├── app/
│   │   ├── api/            # API эндпоинты
│   │   ├── auth/           # Аутентификация
│   │   ├── core/           # Конфигурация и зависимости
│   │   ├── crud/           # Бизнес-логика
│   │   ├── models/         # SQLAlchemy модели
│   │   └── schemas/        # Pydantic схемы
│   ├── main.py             # Точка входа
│   ├── requirements.txt    # Зависимости
│   └── .env.example       # Пример конфигурации
├── frontend/               # Фронтенд на React
│   ├── src/
│   │   ├── components/     # UI компоненты
│   │   ├── pages/         # Страницы
│   │   ├── hooks/         # Кастомные хуки
│   │   ├── types/         # TypeScript типы
│   │   └── api/           # API клиент
│   ├── package.json       # Зависимости
│   └── vite.config.ts     # Конфигурация Vite
├── docker-compose.yml     # Docker Compose
└── README.md              # Документация
```

## Технологии

### Бэкенд
- **FastAPI** — асинхронный веб-фреймворк
- **SQLAlchemy** — ORM для работы с PostgreSQL
- **Pydantic** — валидация данных
- **PostgreSQL** — база данных
- **JWT** — аутентификация
- **Uvicorn** — ASGI сервер
- **Alembic** — миграции базы данных

### Фронтенд
- **React 18** — UI библиотека
- **TypeScript** — статическая типизация
- **Bootstrap 5** — CSS фреймворк
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
- Фронтенд: http://localhost:3000
- API документация: http://localhost:8000/docs

### Ручной запуск (для разработки)

#### Бэкенд
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Фронтенд
```bash
cd frontend
npm install
npm run dev
```

## API Эндпоинты

### Аутентификация
- `POST /auth/token` — Получение JWT токена
- `POST /auth/register` — Регистрация пользователя

### Шаблоны (Templates)
- `GET /api/templates/` — Получение всех шаблонов
- `POST /api/templates/` — Создание шаблона
- `PUT /api/templates/{id}` — Обновление шаблона
- `DELETE /api/templates/{id}` — Удаление шаблона
- `DELETE /api/templates/clear-all` — Очистка всех шаблонов

### Индикаторы (Indicators)
- `GET /api/indicators/` — Получение всех индикаторов
- `POST /api/indicators/` — Создание индикатора
- `PUT /api/indicators/{id}` — Обновление индикатора
- `DELETE /api/indicators/{id}` — Удаление индикатора

### Библиотека индикаторов (Indicator Library)
- `GET /api/indicator-library/` — Получение библиотеки индикаторов
- `POST /api/indicator-library/` — Создание библиотеки
- `GET /api/indicator-library/{id}/versions` — Получение версий библиотеки
- `POST /api/indicator-library/{id}/versions` — Создание версии библиотеки

### Пресеты (Presets)
- `GET /api/presets/` — Получение всех пресетов
- `POST /api/presets/` — Создание пресета
- `PUT /api/presets/{id}` — Обновление пресета
- `DELETE /api/presets/{id}` — Удаление пресета

### Отчёты (Reports)
- `GET /api/reports/` — Получение списка отчётов
- `POST /api/reports/` — Создание отчёта
- `GET /api/reports/{id}` — Получение детальной информации об отчёте
- `GET /api/reports/filtered/list` — Отчёты с фильтрацией
- `DELETE /api/reports/history/clear` — Очистка истории

### Статистика
- `GET /api/statistics/` — Получение статистики по отчётам

## Модели данных

### Пользователь (User)
- id: int
- username: str
- email: str
- is_admin: bool
- hashed_password: str

### Шаблон анализа (AnalysisType)
- id: int
- name: str
- description: str
- created_by: int
- is_active: bool
- indicators: List[Indicator]

### Индикатор (Indicator)
- id: int
- name: str
- unit: str
- min_value: float | null
- max_value: float | null
- data_type: str ('number', 'text', 'select')
- options: str | null (JSON для select)
- analysis_type_id: int

### Библиотека индикаторов (IndicatorLibrary)
- id: int
- name: str
- description: str
- created_by: int
- is_active: bool

### Версия библиотеки (IndicatorLibraryVersion)
- id: int
- library_id: int
- version: str
- description: str
- created_at: datetime
- indicators: List[Indicator]

### Пресет (Preset)
- id: int
- name: str
- description: str
- analysis_type_id: int
- created_by: int
- is_active: bool
- indicators: List[Indicator]

### Отчёт (ProcessLog)
- id: int
- batch_number: str
- analysis_type_id: int
- created_by: int
- status: str ('pending', 'completed', 'failed')
- started_at: datetime
- notes: str | null

### Значение показателя (IndicatorValue)
- id: int
- indicator_id: int
- value: float | null
- text_value: str | null
- is_normal: bool
- process_log_id: int

### Индикатор шаблона (TemplateIndicator)
- id: int
- template_id: int
- indicator_id: int
- order: int

## Роли пользователей

### Администратор
- Доступ ко всем шаблонам
- Управление пользователями
- Полный доступ к отчётам

### Пользователь
- Доступ только к своим отчётам
- Создание шаблонов (если разрешено)
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

## Лицензия

[MIT License](LICENSE)

## Контакты

Для вопросов и предложений:
- Email: your-email@example.com
- GitHub Issues: [wwwanalys/issues](https://github.com/lunevalexsandr-web/wwwanalys/issues)

---

**WWWAnalys v3.0.0** — Система для управления анализами и шаблонами показателей с библиотекой индикаторов
