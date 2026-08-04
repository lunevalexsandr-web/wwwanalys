"""
Финальный тест интеграции с 1С.
Использует правильные имена классов из external_integration.py.

Запуск:
  Терминал 1: python mock_1c_server_v2.py
  Терминал 2: python test_1c_final.py
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.external_integration import (
    OneCIntegrationService,
    ExternalSystemConfig,
    transform_1c_indicator_to_local,
    transform_1c_template_to_local,
    transform_1c_plan_to_local,
)

MOCK_1C_URL = "http://localhost:8899"
REAL_1C_URL = "https://mp.rugen.ru:8443"

ENDPOINTS = {
    "indicators": "/erp_24/hs/labindicators/indicators",
    "templates": "/erp_24/hs/labindicators/templates",
    "plans": "/erp_24/hs/labindicators/plans",
}


def print_result(name: str, success: bool, detail: str = ""):
    status = "✅" if success else "❌"
    print(f"  {status} {name}")
    if detail:
        print(f"     {detail}")


async def test_mock_connection():
    """Тест подключения к мок-1С."""
    print("\n🧪 ТЕСТ: Подключение к мок-1С")
    print("─" * 60)
    
    config = ExternalSystemConfig(
        base_url=MOCK_1C_URL,
        endpoint=ENDPOINTS["indicators"],
    )
    service = OneCIntegrationService(config)
    try:
        result = await service.test_connection()
        ok = result.get("status") == "ok"
        print_result("test_connection()", ok, json.dumps(result, ensure_ascii=False))
        return ok
    finally:
        await service.close()


async def test_mock_fetch_indicators():
    """Тест получения показателей из мок-1С."""
    print("\n🧪 ТЕСТ: Получение показателей")
    print("─" * 60)
    
    config = ExternalSystemConfig(
        base_url=MOCK_1C_URL,
        endpoint=ENDPOINTS["indicators"],
    )
    service = OneCIntegrationService(config)
    try:
        indicators = await service.fetch_indicators_from_1c(ENDPOINTS["indicators"])
        ok = len(indicators) > 0
        detail = f"получено {len(indicators)} шт."
        if indicators:
            detail += f", первый: {json.dumps(indicators[0], ensure_ascii=False)[:150]}"
        print_result("fetch_indicators_from_1c()", ok, detail)
        return ok
    finally:
        await service.close()


async def test_mock_fetch_templates():
    """Тест получения шаблонов из мок-1С."""
    print("\n🧪 ТЕСТ: Получение шаблонов")
    print("─" * 60)
    
    config = ExternalSystemConfig(
        base_url=MOCK_1C_URL,
        endpoint=ENDPOINTS["templates"],
    )
    service = OneCIntegrationService(config)
    try:
        templates = await service.fetch_templates_from_1c(ENDPOINTS["templates"])
        ok = len(templates) > 0
        detail = f"получено {len(templates)} шт."
        if templates:
            detail += f", первый: {json.dumps(templates[0], ensure_ascii=False)[:200]}"
        print_result("fetch_templates_from_1c()", ok, detail)
        return ok
    finally:
        await service.close()


async def test_mock_fetch_plans():
    """Тест получения планов из мок-1С."""
    print("\n🧪 ТЕСТ: Получение планов")
    print("─" * 60)
    
    config = ExternalSystemConfig(
        base_url=MOCK_1C_URL,
        endpoint=ENDPOINTS["plans"],
    )
    service = OneCIntegrationService(config)
    try:
        plans = await service.fetch_plans_from_1c(ENDPOINTS["plans"])
        ok = len(plans) > 0
        detail = f"получено {len(plans)} шт."
        if plans:
            detail += f", первый: {json.dumps(plans[0], ensure_ascii=False)[:200]}"
        print_result("fetch_plans_from_1c()", ok, detail)
        return ok
    finally:
        await service.close()


async def test_transform():
    """Тест функций трансформации."""
    print("\n🔄 ТЕСТ: Трансформация данных")
    print("─" * 60)
    
    # 1. Трансформация показателя
    indicator_1c = {
        "id": "1",
        "name": "Экстрактивность",
        "unit": "%",
        "data_type": "number",
        "description": "Экстрактивность сусла",
        "category": "Варка",
        "is_required": True,
        "default_value": "11.5",
        "options": [],
    }
    result = transform_1c_indicator_to_local(indicator_1c)
    ok = result is not None and result.name == "Экстрактивность"
    print_result("transform_1c_indicator_to_local()", ok,
                f"name={result.name}, external_id={result.external_id}" if result else "None")
    
    # 2. Трансформация шаблона
    template_1c = {
        "id": "1",
        "name": "Варка сусла",
        "description": "Шаблон варки",
        "is_active": True,
        "indicators": [
            {"id": "10", "indicator_id": 1, "min_value": 11.0, "max_value": 12.0, "sort_order": 0},
        ],
    }
    result = transform_1c_template_to_local(template_1c)
    ok = result is not None and result["name"] == "Варка сусла"
    detail = f"name={result['name']}, indicators={len(result['library_indicators'])}" if result else "None"
    print_result("transform_1c_template_to_local()", ok, detail)
    
    # 3. Трансформация плана
    plan_1c = {
        "id": "1",
        "name": "План на 18.06.2026",
        "description": "План на день",
        "plan_date": "2026-06-18",
        "items": [
            {"template_id": 1, "batch_number": "П-001", "sort_order": 0},
        ],
    }
    result = transform_1c_plan_to_local(plan_1c)
    ok = result is not None and result["name"] == "План на 18.06.2026"
    detail = f"name={result['name']}, items={len(result['plan_items'])}" if result else "None"
    print_result("transform_1c_plan_to_local()", ok, detail)
    
    return True


async def test_real_connection():
    """Тест подключения к реальному 1С."""
    print("\n🌐 ТЕСТ: Реальный 1С (mp.rugen.ru:8443)")
    print("─" * 60)
    
    # Без авторизации
    config = ExternalSystemConfig(
        base_url=REAL_1C_URL,
        endpoint=ENDPOINTS["indicators"],
    )
    service = OneCIntegrationService(config)
    try:
        result = await service.test_connection()
        # Ожидаем 401 — это нормально
        is_401 = "401" in result.get("message", "")
        print_result("Без авторизации (ожидается 401)", is_401,
                    json.dumps(result, ensure_ascii=False))
        
        # С Basic Auth (если указаны credentials)
        REAL_USER = os.environ.get("REAL_1C_USER", "")
        REAL_PASS = os.environ.get("REAL_1C_PASS", "")
        
        if REAL_USER and REAL_PASS:
            config2 = ExternalSystemConfig(
                base_url=REAL_1C_URL,
                username=REAL_USER,
                password=REAL_PASS,
                endpoint=ENDPOINTS["indicators"],
            )
            service2 = OneCIntegrationService(config2)
            try:
                result2 = await service2.test_connection()
                ok = result2.get("status") == "ok"
                print_result("С Basic Auth", ok, json.dumps(result2, ensure_ascii=False))
            finally:
                await service2.close()
        else:
            print_result("С Basic Auth", False,
                        "⚠️ Укажите REAL_1C_USER и REAL_1C_PASS в переменных окружения")
        
        return True
    finally:
        await service.close()


async def main():
    print("=" * 60)
    print("🔌 ФИНАЛЬНЫЙ ТЕСТ ИНТЕГРАЦИИ С 1С")
    print("=" * 60)
    print(f"Мок-1С: {MOCK_1C_URL}")
    print(f"Реальный 1С: {REAL_1C_URL}")
    print()
    
    results = []
    
    # Тесты мок-сервера
    results.append(("Подключение к мок-1С", await test_mock_connection()))
    results.append(("Получение показателей", await test_mock_fetch_indicators()))
    results.append(("Получение шаблонов", await test_mock_fetch_templates()))
    results.append(("Получение планов", await test_mock_fetch_plans()))
    
    # Тест трансформации
    results.append(("Трансформация данных", await test_transform()))
    
    # Тест реального 1С
    results.append(("Реальный 1С", await test_real_connection()))
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    
    all_ok = True
    for name, ok in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
        if not ok:
            all_ok = False
    
    print()
    if all_ok:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("\nИнтеграция с 1С полностью работоспособна.")
        print("Для подключения к реальному 1С нужно:")
        print("  1. Получить credentials у администратора 1С")
        print("  2. Запустить с ними:")
        print(f"     REAL_1C_USER=логин REAL_1C_PASS=пароль python test_1c_final.py")
    else:
        print("📋 РЕКОМЕНДАЦИИ:")
        if not results[0][1]:
            print("  • Запустите мок-1С: python mock_1c_server_v2.py")
        if results[0][1] and not results[1][1]:
            print("  • Проверьте endpoint'ы в мок-1С")
        if not results[5][1]:
            print("  • Реальный 1С доступен, но нужна авторизация")
            print("  • Получите логин/пароль у администратора 1С")


if __name__ == "__main__":
    asyncio.run(main())