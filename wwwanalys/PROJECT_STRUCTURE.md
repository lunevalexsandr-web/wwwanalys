# Структура проекта WWWAnalys

Проект представляет собой веб-приложение для сбора, анализа и хранения данных различных показателей с библиотекой индикаторов, шаблонами анализа, планами и двусторонней интеграцией с внешними системами (1С Предприятие). Версия: **6.7.0**.

## Корневая директория

### Конфигурация и документация
- **`README.md`** — основная документация проекта (v6.7.0)
- **`docker-compose.yml`** — конфигурация Docker для запуска приложения
- **`.gitignore`** — правила для игнорирования файлов в Git
- **`AUDIT.md`** — аудит безопасности и архитектуры
- **`PROJECT_STRUCTURE.md`** — данный файл, описание структуры проекта
- **`.copilot-prompt.md`** — системный промпт для AI-ассистентов
- **`docs/API.md`** — документация API

---

## Backend (Python/FastAPI)

### Основные файлы
- **`backend/main.py`** — точка входа приложения, настройка FastAPI, CORS, создание таблиц
- **`backend/requirements.txt`** — зависимости Python
- **`backend/Dockerfile`** — конфигурация Docker для backend
- **`backend/.env.example`** — пример файла окружения
- **`backend/seed.py`** — начальные данные для БД
- **`backend/test_api.py`** — скрипт для тестирования API

### Миграции базы данных
- **`backend/alembic/`** — директория миграций Alembic (требует инициализации)
- **`backend/alembic/versions/`** — файлы версий миграций

### Приложение (`backend/app/`)

#### API эндпоинты (`backend/app/api/`)
| Файл | Префикс | Описание |
|------|---------|----------|
| `auth.py` | `/auth` | Аутентификация и авторизация (JWT, вход, регистрация, текущий пользователь) |
| `indicators.py` | `/api/indicators` | CRUD для библиотеки показателей + импорт/экспорт + версионирование + рекомендации |
| `templates.py` | `/api/templates` | CRUD для шаблонов анализа (admin) |
| `reports.py` | `/api/reports` | CRUD для отчётов |
| `analysis_type.py` | `/analysis-types` | Legacy-алиас шаблонов (требует унификации) |
| `presets.py` | `/api/presets` | Управление пресетами |
| `plans.py` | `/api/plans` | Управление планами анализа |
| `statistics.py` | `/api/statistics` | Эндпоинты статистики |
| `process_log.py` | `/process-logs` | Логирование процессов |
| `external.py` | `/api/external` | Внешние API интеграции (1С: импорт/экспорт/синхронизация) |

#### Сервисы (`backend/app/services/`)
| Файл | Описание |
|------|----------|
| `external_integration.py` | Сервис интеграции с 1С: `OneCIntegrationService`, `ExternalSystemConfig`, импорт показателей/шаблонов/планов, отправка отчётов/планов |

#### Модели данных (`backend/app/models/`)
| Файл | Описание |
|------|----------|
| `user.py` | Модель пользователя |
| `indicator_library.py` | Модель библиотеки показателей |
| `indicator_library_version.py` | Модель версии библиотеки показателей |
| `indicator.py` | Модель показателя |
| `indicator_value.py` | Модель значения показателя |
| `analysis_type.py` | Модель типа анализа (шаблона) |
| `template_indicator.py` | Модель показателя в шаблоне (связь с библиотекой) |
| `report.py` | Модель отчёта |
| `preset.py` | Модель пресета |
| `preset_indicator.py` | Модель связи показателя с пресетом |
| `process_log.py` | Модель лога процесса |
| `analysis_plan.py` | Модель плана анализа |
| `plan_item.py` | Модель элемента плана (template_id, batch_number) |

#### CRUD операции (`backend/app/crud/`)
| Файл | Описание |
|------|----------|
| `user.py` | CRUD для пользователей |
| `indicator_library.py` | CRUD для библиотеки показателей + импорт/экспорт (CSV/Excel/JSON) |
| `indicator_library_version.py` | CRUD для версий библиотеки |
| `report.py` | CRUD для отчётов |
| `analysis_type.py` | CRUD для типов анализа (шаблонов) |
| `preset.py` | CRUD для пресетов |
| `process_log.py` | CRUD для логов процессов |
| `analysis_plan.py` | CRUD для планов анализа |

#### Схемы Pydantic (`backend/app/schemas/`)
| Файл | Описание |
|------|----------|
| `user.py` | Схемы пользователя |
| `indicator_library.py` | Схемы библиотеки показателей (вкл. Batch-схемы) |
| `indicator_library_version.py` | Схемы версий библиотеки |
| `report.py` | Схемы отчётов |
| `analysis_type.py` | Схемы типов анализа (вкл. CopyTemplateRequest, CreateFromPresetRequest) |
| `template_indicator.py` | Схемы показателей в шаблонах |
| `preset.py` | Схемы пресетов |
| `process_log.py` | Схемы логов процессов |
| `analysis_plan.py` | Схемы планов анализа |

#### Ядро приложения (`backend/app/core/`)
| Файл | Описание |
|------|----------|
| `config.py` | Конфигурация приложения (env vars: DATABASE_URL, SECRET_KEY, API_KEY, CORS_ORIGINS) |
| `database.py` | Настройка подключения к БД (SQLAlchemy, сессии) |
| `deps.py` | Зависимости и инъекции (get_db, get_current_user, get_current_active_user, get_current_admin_user) |

#### Аутентификация (`backend/app/auth/`)
| Файл | Описание |
|------|----------|
| `auth.py` | Логика аутентификации (хеширование паролей bcrypt, JWT-токены) |

### Тесты
- **`backend/tests/`** — тесты приложения
- **`backend/tests/test_indicators.py`** — тесты для показателей

---

## Frontend (React 19 / TypeScript)

### Конфигурация
| Файл | Описание |
|------|----------|
| `frontend/package.json` | Зависимости Node.js |
| `frontend/vite.config.ts` | Конфигурация Vite |
| `frontend/tsconfig.json` | Конфигурация TypeScript |
| `frontend/tsconfig.app.json` | Конфигурация TS для приложения |
| `frontend/tsconfig.node.json` | Конфигурация TS для Node |
| `frontend/postcss.config.js` | Конфигурация PostCSS |
| `frontend/eslint.config.js` | Конфигурация ESLint |
| `frontend/Dockerfile` | Конфигурация Docker для frontend |
| `frontend/index.html` | HTML-шаблон приложения |

### Структура исходного кода (`frontend/src/`)

#### Основные файлы
| Файл | Описание |
|------|----------|
| `main.tsx` | Точка входа React приложения |
| `App.tsx` | Основной компонент с маршрутизацией (react-router-dom v7) |
| `App.css` | Стили приложения |
| `index.css` | Глобальные стили (чистый CSS, CSS-переменные, без Bootstrap Icons) |

#### Страницы (`frontend/src/pages/`)
| Файл | Описание |
|------|----------|
| `Login.tsx` | Страница входа (градиентный фон + AuthModal) |
| `Dashboard.tsx` | Панель управления (создание отчётов, история) |
| `Admin.tsx` | Административная панель (только для админов) |
| `Plans.tsx` | Страница планов анализа |

#### Компоненты (`frontend/src/components/`)
| Файл | Описание |
|------|----------|
| `AuthModal.tsx` | Модальное окно авторизации (SaaS-стиль, соц. кнопки) |
| `AppHeader.tsx` | Шапка приложения (навигация, профиль) |
| `AppToast.tsx` | Компонент уведомлений (toast) |
| `AlertToast.tsx` | Компонент алертов |
| `PageHeader.tsx` | Заголовок страницы |
| `ActionButtons.tsx` | Кнопки действий |
| `IndicatorInput.tsx` | Ввод показателей |
| `IndicatorPreview.tsx` | Предпросмотр показателей |
| `IndicatorSelector.tsx` | Выбор показателей из библиотеки |
| `TemplateBuilder.tsx` | Конструктор шаблонов анализа |

#### API интеграция (`frontend/src/api/`)
| Файл | Описание |
|------|----------|
| `axios.ts` | Настройка Axios (интерцепторы для токена, обработка 401) |

#### Контекст и хуки
| Файл | Описание |
|------|----------|
| `context/AuthContext.tsx` | Контекст аутентификации (login, logout, user, token) |
| `hooks/useToast.ts` | Хук для управления уведомлениями |

#### Типы TypeScript (`frontend/src/types/`)
| Файл | Описание |
|------|----------|
| `index.ts` | Общие типы и интерфейсы проекта |

#### Ресурсы
- **`frontend/src/assets/`** — изображения и статичные файлы (hero.png, логотипы)
- **`frontend/public/`** — публичные файлы (favicon.svg, icons.svg)

---

## Основные функции

1. **Библиотека показателей** — система управления справочными показателями с категориями, версионированием, поиском, рекомендациями и импортом/экспортом (CSV/JSON/Excel)
2. **Шаблоны анализа** — создание шаблонов из справочника (только для админов)
3. **Планы анализа** — планирование и управление аналитическими планами (PlanItem с batch_number)
4. **Отчёты** — формирование и просмотр отчётов с передачей batch_number из планов
5. **Администрирование** — управление пользователями, библиотекой, интеграциями (только для админов)
6. **Аутентификация** — система входа через модальное окно (JWT, соц. сети)
7. **Интеграция с 1С** — двусторонний обмен: импорт справочника/шаблонов/планов и экспорт отчётов/планов
8. **Импорт/Экспорт** — загрузка и выгрузка показателей (CSV, JSON, Excel)
9. **Логирование процессов** — отслеживание действий и процессов (ProcessLog)
10. **Статистика** — аналитическая статистика по показателям

---

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React 19)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │  Pages   │ │Components│ │ Context  │ │   API     │  │
│  │Dashboard │ │AuthModal │ │  Auth    │ │  axios    │  │
│  │  Admin   │ │ Header   │ │  Toast   │ │           │  │
│  │  Login   │ │Indicator │ │          │ │           │  │
│  │  Plans   │ │Template  │ │          │ │           │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP (REST API, JWT Bearer)
┌─────────────────────────┴───────────────────────────────┐
│                    Backend (FastAPI)                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │   API    │ │  CRUD    │ │ Models   │ │ Services  │  │
│  │  auth    │ │ user     │ │ user     │ │ external  │  │
│  │indicators│ │ indicator│ │ indicator│ │   (1С)    │  │
│  │ reports  │ │ report   │ │ report   │ │           │  │
│  │ templates│ │ template │ │ template │ │           │  │
│  │  plans   │ │  plan    │ │  plan    │ │           │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌────────────────────────┐  │
│  │ Schemas  │ │  Core    │ │   Auth (JWT)           │  │
│  │ Pydantic │ │ config   │ │   password hashing     │  │
│  │  v2      │ │ database │ │   token generation     │  │
│  │          │ │  deps    │ │                        │  │
│  └──────────┘ └──────────┘ └────────────────────────┘  │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────┐
│              Database (SQLite / PostgreSQL)              │
│              Migrations (Alembic, требует настройки)     │
└─────────────────────────────────────────────────────────┘
```

Архитектура следует слоистому паттерну (API → CRUD → Models/Schemas → Services) с чётким разделением ответственности. Frontend использует компонентный подход с контекстом для управления состоянием аутентификации.