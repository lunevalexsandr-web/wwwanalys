# Интеграция 1С Предприятие → WWWAnalys

Документация по интеграции 1С с проектом WWWAnalys. Поддерживается импорт:
- **Справочника показателей** (`POST /api/external/1c/import-indicators`)
- **Шаблонов анализов** (`POST /api/external/1c/import-templates`) — шаблон загружается «наполненным» (с привязкой к показателям)
- **Планов анализов** (`POST /api/external/1c/import-plans`)

---

## 1. Реальные endpoint 1С

Опубликованный HTTP-сервис 1С доступен по базовому URL:
```
https://mp.rugen.ru:8443
```

Пути (endpoint) HTTP-сервиса 1С:
| Назначение | Endpoint (путь) |
|------------|-----------------|
| Справочник показателей | `/erp_24/hs/labindicators/indicators` |
| Шаблоны анализов | `/erp_24/hs/labindicators/templates` |
| Планы анализов | `/erp_24/hs/labindicators/plans` |

> **Важно:** `base_url` в форме интеграции должен быть `https://mp.rugen.ru:8443`
> (без `/erp_24/hs`). Путь к конкретному HTTP-сервису задаётся отдельным полем
> «Путь к API 1С (endpoint)».

---

## 2. Формат данных от 1С

### 2.1. Показатели (`/erp_24/hs/labindicators/indicators`)

JSON-массив объектов:
```json
[
  {
    "id": "1",
    "name": "Экстрактивность",
    "unit": "%",
    "data_type": "number",
    "description": "Экстрактивность сусла",
    "category": "Варка",
    "is_required": true,
    "default_value": "11.5",
    "options": []
  }
]
```

| Ключ JSON    | Тип          | Описание |
|--------------|--------------|----------|
| `id`         | string       | **ID показателя в 1С** (сохраняется в `indicator_library.external_id`) |
| `name`       | string       | Наименование показателя (обязательно) |
| `unit`       | string       | Единица измерения |
| `data_type`  | string       | `number` \| `text` \| `select` |
| `description`| string       | Описание |
| `category`   | string       | Категория |
| `is_required`| boolean      | Обязательный показатель |
| `default_value` | string    | Значение по умолчанию |
| `options`    | array[string]| Варианты для типа `select` |

### 2.2. Шаблоны анализов (`/erp_24/hs/labindicators/templates`)

JSON-массив объектов:
```json
[
  {
    "id": "1",
    "name": "Варка сусла",
    "description": "Шаблон варки",
    "is_active": true,
    "indicators": [
      {
        "id": "10",
        "indicator_id": 1,
        "min_value": 11.0,
        "max_value": 12.0,
        "sort_order": 0
      }
    ]
  }
]
```

| Ключ JSON         | Тип          | Описание |
|-------------------|--------------|----------|
| `id`              | string       | **ID шаблона в 1С** (сохраняется в `analysis_types.external_id`) |
| `name`            | string       | Наименование шаблона (обязательно) |
| `description`     | string       | Описание |
| `is_active`       | boolean      | Активен ли шаблон |
| `indicators`      | array        | Список показателей шаблона |
| `indicators[].id` | string       | **ID связи показателя в шаблоне** (сохраняется в `template_indicators.external_id`) |
| `indicators[].indicator_id` | string | **ID показателя в 1С** (используется для сопоставления со справочником через `indicator_library.external_id`) |
| `indicators[].min_value` | number | Нижняя граница нормы |
| `indicators[].max_value` | number | Верхняя граница нормы |
| `indicators[].sort_order` | number | Порядок сортировки |

**Сопоставление показателей:** при импорте шаблона каждый показатель ищется
в справочнике `indicator_library` по `external_id == indicators[].indicator_id`.
Если показатель не найден — он создаётся автоматически с `external_id = indicator_id`.
Шаблон загружается «наполненным» — показатели привязываются к нему через `template_indicators`.

### 2.3. Планы анализов (`/erp_24/hs/labindicators/plans`)

JSON-массив объектов:
```json
[
  {
    "id": "1",
    "name": "План на 18.06.2026",
    "description": "План на день",
    "plan_date": "2026-06-18",
    "items": [
      {"template_id": 1, "batch_number": "П-001", "sort_order": 0}
    ]
  }
]
```

---

## 3. Хранение external_id (ID из 1С)

Для сопоставления данных между 1С и WWWAnalys используются поля `external_id`:

| Таблица | Поле `external_id` | Что хранит |
|---------|-------------------|------------|
| `indicator_library` | `external_id` | ID показателя из 1С |
| `analysis_types` | `external_id` | ID шаблона из 1С |
| `template_indicators` | `external_id` | ID связи показателя в шаблоне из 1С |

При повторном импорте (с `skip_duplicates=false`) записи обновляются по `external_id`,
что позволяет синхронизировать изменения из 1С без дублей.

---

## 4. Вызов импорта с нашей стороны

### 4.1. Импорт показателей
```bash
curl -X POST http://localhost:8000/api/external/1c/import-indicators \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "connection": {
      "base_url": "https://mp.rugen.ru:8443",
      "username": "ИМЯ_ПОЛЬЗОВАТЕЛЯ_1С",
      "password": "ПАРОЛЬ_1С",
      "endpoint": "/erp_24/hs/labindicators/indicators"
    },
    "skip_duplicates": true
  }'
```

### 4.2. Импорт шаблонов (с наполнением)
```bash
curl -X POST http://localhost:8000/api/external/1c/import-templates \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "connection": {
      "base_url": "https://mp.rugen.ru:8443",
      "username": "ИМЯ_ПОЛЬЗОВАТЕЛЯ_1С",
      "password": "ПАРОЛЬ_1С",
      "endpoint": "/erp_24/hs/labindicators/templates"
    },
    "skip_duplicates": true
  }'
```

### 4.3. Импорт планов
```bash
curl -X POST http://localhost:8000/api/external/1c/import-plans \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "connection": {
      "base_url": "https://mp.rugen.ru:8443",
      "username": "ИМЯ_ПОЛЬЗОВАТЕЛЯ_1С",
      "password": "ПАРОЛЬ_1С",
      "endpoint": "/erp_24/hs/labindicators/plans"
    },
    "skip_duplicates": true
  }'
```

Если 1С использует собственный API-ключ (а не Basic Auth), вместо
`username`/`password` передайте `"api_key": "КЛЮЧ_1С"`.

---

## 5. Проверка подключения

```bash
curl -X POST http://localhost:8000/api/external/1c/test-connection \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "connection": {
      "base_url": "https://mp.rugen.ru:8443",
      "username": "ИМЯ_ПОЛЬЗОВАТЕЛЯ_1С",
      "password": "ПАРОЛЬ_1С",
      "endpoint": "/erp_24/hs/labindicators/indicators"
    }
  }'
```

Ответ: `{"status": "ok", ...}` при успехе, либо `{"status": "warning", "message": "1C responded with status 401"}`
если нужны правильные креды, либо `{"status": "error", ...}` при сетевой ошибке.

---

## 6. Примечания

- Если `data_type` в 1С реализован как Перечисление, приведите его к строке.
- Для защиты 1С-сервиса добавьте проверку заголовка `X-API-KEY` или Basic Auth.
- При импорте шаблонов показатели ищутся по `external_id` (ID из 1С). Если показатель
  ещё не загружен через импорт показателей — он создаётся автоматически.
- Форматы данных см. в `transform_1c_indicator_to_local`, `transform_1c_template_to_local`
  и `transform_1c_plan_to_local` в `backend/app/services/external_integration.py`.