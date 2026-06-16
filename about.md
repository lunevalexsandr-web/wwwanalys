- PostgreSQL: localhost:5433

## API Эндпоинты

### Аутентификация

- `POST /auth/token` — Получение JWT токена
- `POST /auth/register` — Регистрация пользователя

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
- template_indicators: List[TemplateIndicator] — показатели из справочника

### Библиотека показателей (IndicatorLibrary)

- id: int
- name: str
- unit: str
- data_type: str ('number', 'text', 'select')
- options: str (JSON для select)
- description: str
- category: str ('quality', 'safety', 'performance', 'chemical', 'physical', 'microbiology')
- is_required: bool
- default_value: str
- validation_rules: str (JSON)
- created_by: int
- created_at: datetime

### Показатель шаблона (TemplateIndicator)

- id: int
- template_id: int
- indicator_id: int (ссылка на IndicatorLibrary)
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
- indicators: List[PresetIndicator]

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
- Переход от плана к созданию отчёта (с передачей шаблона и номера партии)

## Интеграция Plans ↔ Dashboard

### Переход из планирования в создание отчёта

Функция позволяет лаборанту непосредственно из плана анализов перейти к форме создания отчёта с предзаполненными данными:

__Процесс:__

1. На странице __Plans__ пользователь видит список планов на выбранный день

2. Для каждого элемента плана доступна кнопка "Создать отчет"

3. При нажатии происходит:

   - Сохранение ID шаблона и номера партии в `localStorage` (`planItemToReport`)
   - Переход на страницу __Dashboard__
   - Автоматическая установка выбранного шаблона
   - Заполнение номера партии
   - Открытие вкладки "Новый отчет"

__Техническая реализация:__

- Plans.tsx использует `useNavigate` для перехода с передачей state
- Dashboard.tsx использует `useLocation` для получения state и `useEffect` для обработки localStorage
- После обработки localStorage данные автоматически очищаются

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

- __v1.0.0__ — Initial release with admin panel and analysis constructor
- __v2.0.0__ — Save current version
- __v3.0.0__ — Full fix for reports and templates with UI improvements
- __v3.0.0-bootstrap__ — feat: migrate frontend from Tailwind CSS to Bootstrap 5
- __v3.1.0__ — feat: add indicator library with versioning and presets support
- __v3.2.0__ — feat: remove template_type, remove custom indicators, add 1C integration

## Лицензия

[MIT License](LICENSE)

## Контакты

Для вопросов ипредложений:
