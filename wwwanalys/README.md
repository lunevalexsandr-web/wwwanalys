# WWWAnalys - Анализ производства

Веб-приложение для учета производственных анализов на базе Python (FastAPI) + PostgreSQL с фронтендом на HTML/CSS (Tailwind) + JavaScript.

## Стек технологий

### Бэкенд
- Python 3.9+
- FastAPI
- SQLAlchemy
- PostgreSQL (через Docker)
- Pydantic
- JWT-аутентификация

### Фронтенд
- HTML5
- CSS3
- JavaScript (ES6+)
- Bootstrap 5
- Tailwind CSS

## Структура проекта

```
wwwanalys/
├── backend/                  # Бэкенд на FastAPI
│   ├── app/
│   │   ├── api/             # API роуты
│   │   ├── auth/            # Аутентификация
│   │   ├── core/            # Конфигурация и база данных
│   │   ├── crud/            # CRUD операции
│   │   ├── models/          # SQLAlchemy модели
│   │   └── schemas/         # Pydantic схемы
│   ├── main.py              # Основной файл приложения
│   ├── requirements.txt     # Зависимости
│   └── .env.example        # Пример переменных окружения
├── frontend/                # Фронтенд
│   ├── index.html          # Главный HTML файл
│   └── app.js              # JavaScript код
├── docker-compose.yml       # Конфигурация Docker
└── plan.md                 # План проекта
```

## Функциональность

### Роли пользователей
- **Администратор**: Может создавать типы анализов, добавлять индикаторы, управлять пользователями
- **Пользователь**: Может выбирать типы анализов, заполнять значения показателей, просматривать журнал процессов

### Основные возможности
1. **Управление типами анализов**
   - Создание типов анализов
   - Динамическое добавление индикаторов (название, единица измерения, мин/макс значения)
   - Просмотр списка типов анализов

2. **Управление процессами**
   - Создание записей в журнале процессов
   - Выбор типа анализа и ввод значений показателей
   - Отслеживание статуса процессов

3. **Пользователи**
   - Регистрация и аутентификация
   - Управление пользователями (только для администраторов)

## Запуск проекта

### 1. Запуск базы данных (PostgreSQL)

```bash
docker-compose up -d
```

### 2. Установка зависимостей бэкенда

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Для Linux/Mac
# или
venv\Scripts\activate     # Для Windows
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните необходимые значения:

```bash
cp .env.example .env
```

### 4. Запуск бэкенд-приложения

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Запуск фронтенда

Просто откройте файл `frontend/index.html` в браузере.

## API документация

После запуска бэкенда, документация API доступна по адресу:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Примеры использования

### 1. Регистрация пользователя

```bash
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "email": "test@example.com", "password": "password123", "is_active": true, "is_admin": false}'
```

### 2. Аутентификация

```bash
curl -X POST "http://localhost:8000/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=password123"
```

### 3. Создание типа анализа (только администратор)

```bash
curl -X POST "http://localhost:8000/analysis-types/" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"name": "Анализ партии", "description": "Анализ производственной партии", "indicators": [{"name": "Температура", "unit": "°C", "min_value": 20.0, "max_value": 25.0}]}'
```

### 4. Создание записи в журнале процессов

```bash
curl -X POST "http://localhost:8000/process-logs/" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"analysis_type_id": 1, "notes": "Тестовая запись", "indicator_values": [{"indicator_id": 1, "value": 22.5}]}'
```

## Дальнейшее развитие

1. Добавить тесты (Unit и Integration)
2. Реализовать систему уведомлений
3. Добавить графическую визуализацию данных
4. Реализовать импорт/экспорт данных
5. Добавить поддержку нескольких языков
6. Реализовать систему прав доступа более детально

## Лицензия

Этот проект распространяется под лицензией MIT.