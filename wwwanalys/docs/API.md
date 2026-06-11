# API документация WWWAnalys v3.2.0

Base URL: `http://localhost:8000`

## Аутентификация

Все эндпоинты (кроме `/auth/token` и `/auth/register`) требуют JWT токен в заголовке:
```
Authorization: Bearer <token>
```

### POST /auth/token
Получение JWT токена для существующего пользователя.

**Request:**
```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=yourpassword
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### POST /auth/register
Регистрация нового пользователя.

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response 201:**
```json
{
  "id": 2,
  "username": "newuser",
  "email": "user@example.com",
  "is_admin": false
}
```

---

## Шаблоны анализов

Шаблоны содержат только показатели из справочника (library_indicators).

### GET /api/templates/
Получить список всех шаблонов с показателями из справочника.

**Response 200:**
```json
[
  {
    "id": 1,
    "name": "Анализ воды",
    "description": "Стандартный анализ воды",
    "created_by": 1,
    "is_active": true,
    "template_indicators": [
      {
        "id": 1,
        "indicator_id": 1,
        "name": "pH",
        "unit": "pH",
        "data_type": "number",
        "min_value": 6.5,
        "max_value": 8.5,
        "sort_order": 0
      }
    ]
  }
]
```

### GET /api/templates/active
Получить только активные шаблоны.

### GET /api/templates/{template_id}
Получить шаблон по ID.

### POST /api/templates/
Создать новый шаблон. **Только для админа.**

**Request:**
```json
{
  "name": "Анализ почвы",
  "description": "Полный анализ почвы",
  "library_indicators": [
    {
      "indicator_id": 1,
      "min_value": 10,
      "max_value": 80,
      "sort_order": 0
    },
    {
      "indicator_id": 2,
      "min_value": null,
      "max_value": null,
      "sort_order": 1
    }
  ]
}
```

**Response 201:**
```json
{
  "id": 2,
  "name": "Анализ почвы",
  "description": "Полный анализ почвы",
  "created_by": 1,
  "is_active": true,
  "template_indicators": [...]
}
```

### PUT /api/templates/{template_id}
Обновить шаблон. **Только для админа.**

**Request:**
```json
{
  "name": "Обновлённое название",
  "description": "Новое описание",
  "is_active": true,
  "library_indicators": [...]
}
```

### DELETE /api/templates/{template_id}
Удалить шаблон по ID. **Только для админа.**

### DELETE /api/templates/clear-all
Удалить все шаблоны. **Только для админа.**

### POST /api/templates/{template_id}/copy
Копировать шаблон с новым именем. **Только для админа.**

**Request:**
```json
{
  "new_name": "Копия шаблона",
  "new_description": "Описание копии"
}
```

### POST /api/templates/from-preset
Создать шаблон из пресета. **Только для админа.**

**Request:**
```json
{
  "preset_id": 1,
  "template_name": "Новый шаблон из пресета",
  "template_description": "Описание"
}
```

---

## Библиотека показателей (Indicator Library)

Централизованный справочник показателей, который может быть импортирован из внешних систем (1С).

### GET /api/indicators/library
Получить список всех показателей из справочника.

**Query параметры:**
- `search` (string, optional) — Поиск по названию, описанию, категории
- `category` (string, optional) — Фильтр по категории (quality, safety, performance, chemical, physical, microbiology)
- `data_type` (string, optional) — Фильтр по типу данных (number, text, select)
- `skip` (int, default: 0) — Пропустить записей
- `limit` (int, default: 100) — Лимит записей

**Response 200:**
```json
[
  {
    "id": 1,
    "name": "pH",
    "unit": "pH",
    "data_type": "number",
    "description": "Показатель кислотности",
    "category": "quality",
    "is_required": true,
    "default_value": "7.0",
    "created_at": "2026-06-01T10:00:00"
  }
]
```

### POST /api/indicators/library
Создать новый показатель в справочнике. **Только для админа.**

**Request:**
```json
{
  "name": "Влажность",
  "unit": "%",
  "data_type": "number",
  "description": "Показатель влажности",
  "category": "quality",
  "is_required": false,
  "default_value": "0.0"
}
```

### PUT /api/indicators/library/{indicator_id}
Обновить показатель в справочнике. **Только для админа.**

### DELETE /api/indicators/library/{indicator_id}
Удалить показатель из справочника. **Только для админа.**

### POST /api/indicators/library/batch/create
Пакетное создание показателей. **Только для админа.**

**Request:**
```json
{
  "indicators": [
    {
      "name": "Показатель 1",
      "unit": "%",
      "data_type": "number",
      "category": "quality"
    },
    {
      "name": "Показатель 2",
      "unit": "мг/л",
      "data_type": "number",
      "category": "chemical"
    }
  ]
}
```

### GET /api/indicators/library/export/csv
Экспортировать справочник в формате CSV.

### GET /api/indicators/library/export/excel
Экспортировать справочник в формате Excel (.xlsx).

### POST /api/indicators/library/import/csv
Импортировать показатели из CSV-файла.

### POST /api/indicators/library/import/json
Импортировать показатели из JSON-файла.

---

## Интеграция с 1С Предприятие

API для загрузки справочника показателей из внешних систем (1С Предприятие).

**Важно:** Все эндпоинты интеграции требуют заголовок `X-API-KEY` с ключом из конфигурации.

### POST /api/external/1c/test-connection
Проверить подключение к 1С.

**Request:**
```json
{
  "connection": {
    "base_url": "http://1c-server:8080",
    "api_key": "your-api-key",
    "timeout": 30
  }
}
```

**Response 200:**
```json
{
  "status": "ok",
  "message": "Connection to 1C successful",
  "timestamp": "2026-06-06T09:00:00"
}
```

### POST /api/external/1c/import-indicators
Импортировать справочник показателей из 1С.

**Request:**
```json
{
  "connection": {
    "base_url": "http://1c-server:8080",
    "api_key": "your-api-key",
    "username": "admin",
    "password": "password"
  },
  "endpoint": "/api/v1/indicators",
  "field_mapping": {
    "name": "Наименование",
    "unit": "ЕдиницаИзмерения",
    "data_type": "ТипДанных",
    "description": "Описание",
    "category": "Категория"
  },
  "skip_duplicates": true
}
```

**Поля field_mapping:**
- `name` — Название показателя (обязательное)
- `unit` — Единица измерения
- `data_type` — Тип данных (number, text, select)
- `description` — Описание показателя
- `category` — Категория (quality, safety, performance, chemical, physical, microbiology)
- `is_required` — Обязательный показатель
- `default_value` — Значение по умолчанию
- `options` — Варианты для select (через запятую или массив)

**Response 200:**
```json
{
  "status": "success",
  "total": 150,
  "created": 120,
  "skipped": 30,
  "errors": [],
  "timestamp": "2026-06-06T09:05:00"
}
```

### GET /api/external/1c/indicators
Получить список показателей из 1С без сохранения в БД (предпросмотр).

**Query параметры:**
- `base_url` (string, required) — URL сервера 1С
- `api_key` (string, optional) — API-ключ
- `username` (string, optional) — Логин
- `password` (string, optional) — Пароль
- `endpoint` (string, default: /api/v1/indicators) — API-эндпоинт

**Response 200:**
```json
{
  "status": "success",
  "count": 150,
  "indicators": [
    {
      "id": "1",
      "name": "pH",
      "unit": "pH",
      "data_type": "number"
    }
  ]
}
```

---

## Пресеты

### GET /api/presets/
Получить список всех пресетов.

### POST /api/presets/
Создать новый пресет. **Только для админа.**

### PUT /api/presets/{preset_id}
Обновить пресет. **Только для админа.**

### DELETE /api/presets/{preset_id}
Удалить пресет. **Только для админа.**

---

## Отчёты

### GET /api/reports/
Получить список отчётов текущего пользователя (или все для админа).

**Response 200:**
```json
[
  {
    "id": 37,
    "batch_number": "BATCH-001",
    "analysis_type_id": 1,
    "started_at": "2026-06-03T10:50:21",
    "status": "pending",
    "notes": null,
    "values": [],
    "created_by": 1
  }
]
```

### POST /api/reports/
Создать новый отчёт.

**Request:**
```json
{
  "template_id": 1,
  "batch_number": "BATCH-001",
  "values": [
    {
      "indicator_id": 1,
      "value": 7.2
    },
    {
      "indicator_id": 2,
      "value": "Песчаная"
    }
  ]
}
```

### GET /api/reports/{report_id}
Получить детальную информацию об отчёте, включая значения показателей.

### GET /api/reports/filtered/list
Получить отчёты с фильтрацией.

**Query параметры:**
- `template_id` (int, optional) — Фильтр по шаблону
- `date_from` (date, optional) — Начальная дата (YYYY-MM-DD)
- `date_to` (date, optional) — Конечная дата (YYYY-MM-DD)
- `skip` (int, default: 0) — Пропустить записей
- `limit` (int, default: 100) — Лимит записей

### DELETE /api/reports/history/clear
Очистить всю историю отчётов текущего пользователя.

---

## Статистика

### GET /api/statistics/
Получить статистику по отчётам.

**Response 200:**
```json
{
  "total_indicators": 50,
  "by_category": {
    "quality": 20,
    "safety": 15,
    "performance": 15
  },
  "by_type": {
    "number": 30,
    "text": 10,
    "select": 10
  },
  "most_used": [...]
}
```

---

## Типы данных

### DataType (строка)
- `"number"` — Числовое значение
- `"text"` — Текстовое значение
- `"select"` — Выбор из вариантов

### Category (строка)
- `"quality"` — Качество
- `"safety"` — Безопасность
- `"performance"` — Производительность
- `"chemical"` — Химический состав
- `"physical"` — Физические свойства
- `"microbiology"` — Микробиология

### Status (перечисление)
- `"pending"` — В ожидании
- `"in_progress"` — В процессе
- `"completed"` — Завершён
- `"failed"` — Ошибка

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| 400 | Bad Request — неверный запрос |
| 401 | Unauthorized — нет токена или токен недействителен |
| 403 | Forbidden — нет прав доступа |
| 404 | Not Found — ресурс не найден |
| 500 | Internal Server Error — внутренняя ошибка сервера |

---

## Примеры использования

### JavaScript / TypeScript
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

// Установка токена
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Создание отчёта
const createReport = async () => {
  const response = await api.post('/api/reports/', {
    template_id: 1,
    batch_number: 'BATCH-001',
    values: [
      { indicator_id: 1, value: 7.2 }
    ]
  });
  return response.data;
};

// Импорт из 1С
const importFrom1C = async () => {
  const response = await api.post('/api/external/1c/import-indicators', {
    connection: {
      base_url: 'http://1c-server:8080',
      api_key: 'your-api-key'
    },
    skip_duplicates: true
  });
  return response.data;
};
```

### cURL
```bash
# Получить токен
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=admin&password=password' | jq -r '.access_token')

# Получить шаблоны
curl -s http://localhost:8000/api/templates/ \
  -H "Authorization: Bearer $TOKEN"

# Создать отчёт
curl -s -X POST http://localhost:8000/api/reports/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 1,
    "batch_number": "BATCH-001",
    "values": [{"indicator_id": 1, "value": 7.2}]
  }'

# Проверить подключение к 1С
curl -s -X POST http://localhost:8000/api/external/1c/test-connection \
  -H "X-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"connection": {"base_url": "http://1c-server:8080"}}'

# Импорт показателей из 1С
curl -s -X POST http://localhost:8000/api/external/1c/import-indicators \
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

---

**API документация WWWAnalys v3.2.0** | Автогенерируемая документация: http://localhost:8000/docs