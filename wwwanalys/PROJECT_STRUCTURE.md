# Структура проекта WWWAnalys

Проект представляет собой веб-приложение для сбора, анализа и хранения данных различных показателей с разделением на backend (Python/FastAPI) и frontend (React/TypeScript).

## Корневая директория

### Конфигурация и документация
- **`README.md`** - основная документация проекта
- **`docker-compose.yml`** - конфигурация Docker для запуска приложения
- **`.gitignore`** - правила для игнорирования файлов в Git
- **`AUDIT.md`** - аудит безопасности
- **`docs/API.md`** - документация API

### Backend (Python/FastAPI)

#### Основные файлы
- **`backend/main.py`** - точка входа приложения, настройка FastAPI
- **`backend/requirements.txt`** - зависимости Python
- **`backend/Dockerfile`** - конфигурация Docker для backend
- **`backend/.env.example`** - пример файла окружения

#### Миграции базы данных
- **`backend/alembic/`** - директория миграций Alembic
- **`backend/seed.py`** - начальные данные для БД

#### Приложение (`backend/app/`)

**API эндпоинты (`backend/app/api/`)**
- **`indicators.py`** - API для работы с показателями и библиотекой показателей
- **`templates.py`** - API для работы с шаблонами анализа
- **`reports.py`** - API для работы с отчетами
- **`auth.py`** - аутентификация и авторизация
- **`analysis_type.py`** - API для типов анализа
- **`presets.py`** - API для пресетов
- **`statistics.py`** - API для статистики
- **`process_log.py`** - API для логов процессов
- **`external.py`** - внешние API интеграции

**Модели данных (`backend/app/models/`)**
- **`indicator.py`** - модель показателя
- **`indicator_library.py`** - модель библиотеки показателей
- **`indicator_library_version.py`** - модель версии библиотеки
- **`indicator_value.py`** - модель значения показателя
- **`analysis_type.py`** - модель типа анализа
- **`template_indicator.py`** - модель показателя в шаблоне
- **`report.py`** - модель отчета
- **`preset.py`** - модель пресета
- **`process_log.py`** - модель лога процесса
- **`user.py`** - модель пользователя

**CRUD операции (`backend/app/crud/`)**
- **`indicator.py`** - CRUD для показателей
- **`indicator_library.py`** - CRUD для библиотеки показателей
- **`report.py`** - CRUD для отчетов
- **`analysis_type.py`** - CRUD для типов анализа
- **`template_indicator.py`** - CRUD для показателей в шаблонах
- **`preset.py`** - CRUD для пресетов
- **`process_log.py`** - CRUD для логов
- **`user.py`** - CRUD для пользователей

**Схемы Pydantic (`backend/app/schemas/`)**
- Аналогичны моделям, но для валидации данных API

**Ядро приложения (`backend/app/core/`)**
- **`config.py`** - конфигурация приложения
- **`database.py`** - настройка подключения к БД
- **`deps.py`** - зависимости и инъекции

**Аутентификация (`backend/app/auth/`)**
- **`auth.py`** - логика аутентификации

#### Тесты
- **`backend/tests/`** - тесты приложения

### Frontend (React/TypeScript)

#### Конфигурация
- **`frontend/package.json`** - зависимости Node.js
- **`frontend/vite.config.ts`** - конфигурация Vite
- **`frontend/tsconfig.json`** - конфигурация TypeScript
- **`frontend/postcss.config.js`** - конфигурация PostCSS
- **`frontend/tailwind.config.js`** - конфигурация Tailwind CSS
- **`frontend/Dockerfile`** - конфигурация Docker для frontend

#### Структура исходного кода (`frontend/src/`)

**Основные файлы**
- **`main.tsx`** - точка входа React приложения
- **`App.tsx`** - основной компонент приложения с маршрутизацией
- **`index.css`** - глобальные стили

**Страницы (`frontend/src/pages/`)**
- **`Dashboard.tsx`** - панель управления (создание отчетов, история)
- **`Admin.tsx`** - административная панель
- **`Login.tsx`** - страница входа

**Компоненты (`frontend/src/components/`)**
- **`AppHeader.tsx`** - шапка приложения
- **`AppToast.tsx`** - компонент уведомлений
- **`AlertToast.tsx`** - компонент алертов
- **`IndicatorInput.tsx`** - ввод показателей
- **`IndicatorPreview.tsx`** - предпросмотр показателей
- **`IndicatorSelector.tsx`** - выбор показателей
- **`TemplateBuilder.tsx`** - конструктор шаблонов
- **`PageHeader.tsx`** - заголовок страницы
- **`ActionButtons.tsx`** - кнопки действий

**API интеграция (`frontend/src/api/`)**
- **`axios.ts`** - настройка Axios для HTTP запросов

**Контекст и хуки (`frontend/src/context/`, `frontend/src/hooks/`)**
- **`AuthContext.tsx`** - контекст аутентификации
- **`useToast.ts`** - хук для уведомлений

**Типы TypeScript (`frontend/src/types/`)**
- **`index.ts`** - общие типы проекта

**Ресурсы (`frontend/src/assets/`)**
- Изображения и статичные файлы

**Публичные файлы (`frontend/public/`)**
- Favicon и иконки

## Основные функции

1. **Библиотека показателей** - система управления справочными показателями
2. **Шаблоны анализа** - создание шаблонов для различных типов анализа
3. **Отчеты** - формирование и просмотр отчетов
4. **Администрирование** - управление пользователями и настройками
5. **Аутентификация** - система входа и управления пользователями

Архитектура следует паттерну MVC с разделением API, моделей, CRUD операций и пользовательского интерфейса.