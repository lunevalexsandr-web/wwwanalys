# API документация WWWAnalys v3.0.0

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

### GET /api/templates/
Получить список всех шаблонов с индикаторами.

**Response 200:**
```json
[
  {
    "id": 1,
    "name": "Анализ воды",
    "description": "Стандартный анализ воды",
    "created_by": 1,
    "is_active": true,
    "indicators": [
      {
        "id": 1,
        "name": "pH",
        "unit": "pH",
        "min_value": 6.5,
        "max_value": 8.5,
        "data_type": "number",
        "options": null
      }
    ]
  }
]
```

### GET /api/templates/active
Получить только активные шаблоны.

### POST /api/templates/
Создать новый шаблон. **Только для админа.**

**Request:**
```json
{
  "name": "Анаализ почвы",
  "description": "Полный анализ почвы",
  "indicators": [
    {
      "name": "Влажность",
      "unit": "%",
      "min_value": 10,
      "max_value": 80,
      "data_type": "number"
    },
    {
      "name": "Тип почвы",
      "unit": "",
      "min_value": null,
      "max_value": null,
      "data_type": "select",
      "options": ["Песчаная", "Суглинистая", "Глинистая"]
    }
  ]
}
```

**Response 201:**
```json
{
  "id": 2,
  "name": "Анаализ почвы",
  "description": "Полный анализ почвы",
  "created_by": 1,
  "is_active": true,
  "indicators": [...]
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
  "indicators": [...]
}
```

### DELETE /api/templates/{template_id}
Удалить шаблон по ID. **Только для админа.**

**Response 200:**
```json
{
  "message": "Template deleted successfully"
}
```

### DELETE /api/templates/clear-all
Удалить все шаблоны. **Только для админа.**

**Response 200:**
```json
{
  "message": "Удалено шаблонов: 12",
  "deleted_count": 12
}
```

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

**Response 201:**
```json
{
  "id": 38,
  "batch_number": "BATCH-001",
  "analysis_type_id": 1,
  "started_at": "2026-06-03T11:00:00",
  "status": "pending",
  "notes": null,
  "values": []
}
```

### GET /api/reports/{report_id}
Получить детальную информацию об отчёте, включая значения показателей.

**Response 200:**
```json
{
  "id": 37,
  "batch_number": "BATCH-001",
  "analysis_type_id": 1,
  "started_at": "2026-06-03T10:50:21",
  "status": "pending",
  "notes": null,
  "created_by": 1,
  "values": [
    {
      "id": 54,
      "indicator_id": 1,
      "value": 5.0,
      "text_value": null,
      "is_normal": true
    }
  ]
}
```

### GET /api/reports/filtered/list
Получить отчёты с фильтрацией.

**Query параметры:**
- `template_id` (int, optional) — Фильтр по шаблону
- `date_from` (date, optional) — Начальная дата (YYYY-MM-DD)
- `date_to` (date, optional) — Конечная дата (YYYY-MM-DD)
- `skip` (int, default: 0) — Пропустить записей
- `limit` (int, default: 100) — Лимит записей

**Пример:**
```
GET /api/reports/filtered/list?template_id=1&date_from=2026-01-01&date_to=2026-12-31
```

### DELETE /api/reports/history/clear
Очистить всю историю отчётов текущего пользователя.

**Response 200:**
```json
{
  "message": "All reports deleted successfully"
}
```

---

## Типы данных

### DataType (строка)
- `"number"` — Числовое значение
- `"text"` — Текстовое значение
- `"select"` — Выбор из вариантов

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
```

---

**API документация WWWAnalys v3.0.0** | Автогенерируемая документация: http://localhost:8000/docs