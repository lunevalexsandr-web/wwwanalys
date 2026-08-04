"""
Прямой тест подключения к 1С (без бэкенда).
Проверяет OData/HTTP-сервис 1С напрямую.

Запуск: python test_1c_connection_direct.py

Использует только httpx — не требует БД, бэкенд, Docker.
"""
import httpx
import json
import asyncio
import sys

# Конфигурация
MOCK_1C_URL = "http://localhost:8899"
REAL_1C_URL = "https://mp.rugen.ru:8443"

# Endpoints как в документации
ENDPOINTS = {
    "indicators": "/erp_24/hs/labindicators/indicators",
    "templates": "/erp_24/hs/labindicators/templates",
    "plans": "/erp_24/hs/labindicators/plans",
}

# ⚠️ СЮДА ВСТАВЬТЕ РЕАЛЬНЫЕ ДАННЫЕ ДЛЯ ПОДКЛЮЧЕНИЯ К 1С
REAL_1C_USER = "1c_user"     # <-- замените на реальный логин
REAL_1C_PASS = "1c_pass"     # <-- замените на реальный пароль
REAL_1C_API_KEY = ""         # <-- если используется API key вместо Basic Auth


def print_result(name: str, success: bool, detail: str = ""):
    status = "✅" if success else "❌"
    print(f"  {status} {name}")
    if detail:
        print(f"     {detail}")


async def test_mock_server():
    """Тест мок-сервера 1С (localhost:8899)."""
    print("\n" + "=" * 60)
    print("🧪 ТЕСТ 1: МОК-СЕРВЕР 1С (localhost:8899)")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=5) as client:
        all_ok = True
        for name, path in ENDPOINTS.items():
            try:
                resp = await client.get(f"{MOCK_1C_URL}{path}")
                ok = resp.status_code == 200
                data = resp.json()
                count = len(data) if isinstance(data, list) else 1
                print_result(f"{name} (HTTP {resp.status_code})", ok,
                           f"получено {count} записей")
                if not ok:
                    all_ok = False
            except Exception as e:
                print_result(name, False, str(e))
                all_ok = False
        return all_ok


async def test_real_1c():
    """Тест реального сервера 1С (mp.rugen.ru:8443)."""
    print("\n" + "=" * 60)
    print("🌐 ТЕСТ 2: РЕАЛЬНЫЙ 1С (mp.rugen.ru:8443)")
    print("=" * 60)

    # 2.1 Без авторизации (ожидаем 401)
    print("\n--- 2.1 Без авторизации (ожидается 401) ---")
    async with httpx.AsyncClient(verify=False, timeout=10) as client:
        for name, path in ENDPOINTS.items():
            try:
                resp = await client.get(f"{REAL_1C_URL}{path}")
                is_401 = resp.status_code == 401
                print_result(f"{name} (HTTP {resp.status_code})", is_401,
                           "нет авторизации — ожидаем 401")
            except Exception as e:
                print_result(name, False, str(e))

    # 2.2 С Basic Auth
    print("\n--- 2.2 С Basic Auth ---")
    import base64
    if REAL_1C_USER and REAL_1C_PASS:
        credentials = base64.b64encode(f"{REAL_1C_USER}:{REAL_1C_PASS}".encode()).decode()
        headers = {"Authorization": f"Basic {credentials}"}
        async with httpx.AsyncClient(verify=False, timeout=10, headers=headers) as client:
            for name, path in ENDPOINTS.items():
                try:
                    resp = await client.get(f"{REAL_1C_URL}{path}")
                    ok = resp.status_code == 200
                    detail = f"HTTP {resp.status_code}"
                    if ok:
                        data = resp.json()
                        count = len(data) if isinstance(data, list) else 1
                        detail += f", получено {count} записей"
                    print_result(f"{name} (Basic Auth)", ok, detail)
                except Exception as e:
                    print_result(name, False, str(e))
    else:
        print_result("Basic Auth", False, "❌ НЕ УКАЗАНЫ LOGIN/PASS")
        print("     Укажите REAL_1C_USER и REAL_1C_PASS в файле test_1c_connection_direct.py")

    # 2.3 С API Key
    print("\n--- 2.3 С X-API-KEY ---")
    if REAL_1C_API_KEY:
        headers = {"X-API-KEY": REAL_1C_API_KEY}
        async with httpx.AsyncClient(verify=False, timeout=10, headers=headers) as client:
            for name, path in ENDPOINTS.items():
                try:
                    resp = await client.get(f"{REAL_1C_URL}{path}")
                    ok = resp.status_code == 200
                    detail = f"HTTP {resp.status_code}"
                    if ok:
                        data = resp.json()
                        count = len(data) if isinstance(data, list) else 1
                        detail += f", получено {count} записей"
                    print_result(f"{name} (X-API-KEY)", ok, detail)
                except Exception as e:
                    print_result(name, False, str(e))
    else:
        print_result("X-API-KEY", False, "⚠️ API KEY не указан (пропускаем)")


async def test_odata_query():
    """Тест OData-стиля запросов (если 1С использует OData)."""
    print("\n" + "=" * 60)
    print("🔍 ТЕСТ 3: OData-СТИЛЬ ЗАПРОСОВ")
    print("=" * 60)

    # Некоторые 1С публикуют OData-сервисы с другим форматом URL
    odata_endpoints = {
        "indicators": "/erp_24/odata/standard.odata/Catalog_Показатели",
        "templates": "/erp_24/odata/standard.odata/Catalog_ШаблоныАнализов",
        "plans": "/erp_24/odata/standard.odata/Document_ПланыАнализов",
    }

    async with httpx.AsyncClient(verify=False, timeout=10) as client:
        for name, path in odata_endpoints.items():
            try:
                resp = await client.get(f"{REAL_1C_URL}{path}")
                ok = resp.status_code == 200
                detail = f"HTTP {resp.status_code}"
                if ok:
                    data = resp.json()
                    if isinstance(data, dict) and "value" in data:
                        detail += f", OData value count: {len(data['value'])}"
                print_result(f"{name} (OData)", ok, detail)
            except Exception as e:
                print_result(f"{name} (OData)", False, str(e))


async def main():
    print("=" * 60)
    print("🔌 ТЕСТ ПОДКЛЮЧЕНИЯ К 1С (OData/HTTP-сервис)")
    print("=" * 60)
    print(f"\nМок-1С: {MOCK_1C_URL}")
    print(f"Реальный 1С: {REAL_1C_URL}")

    results = []
    results.append(("Мок-сервер 1С", await test_mock_server()))
    results.append(("Реальный 1С", await test_real_1c()))
    results.append(("OData-стиль", await test_odata_query()))

    print("\n" + "=" * 60)
    print("📊 ИТОГИ")
    print("=" * 60)
    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")

    print("\n" + "─" * 60)
    print("💡 ЧТО ДАЛЬШЕ:")
    print("  1. Если мок-сервер работает — интеграция через бэкенд будет работать")
    print("     после настройки сети (host.docker.internal или локальный запуск)")
    print("  2. Если реальный 1С отвечает 200 с credentials — всё готово к импорту")
    print("  3. Если реальный 1С отвечает 401 — нужны правильные логин/пароль")
    print("  4. Если реальный 1С не отвечает — проверьте URL и сетевую доступность")


if __name__ == "__main__":
    asyncio.run(main())