"""
Тест подключения к 1С по OData с реальными credentials.
Пароль вводится через переменную окружения (не сохраняется в файл).

Запуск:
  REAL_1C_USER=obmenapi1c REAL_1C_PASS=Qasd33!! python test_1c_odata.py
"""
import asyncio
import json
import os
import sys
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.external_integration import (
    OneCIntegrationService,
    ExternalSystemConfig,
)

REAL_1C_URL = "https://mp.rugen.ru:8443"

# OData endpoint'ы (стандартные для 1С)
ODATA_ENDPOINTS = {
    "Показатели (OData)": "/erp_24/odata/standard.odata/Catalog_Показатели",
    "Шаблоны (OData)": "/erp_24/odata/standard.odata/Catalog_ШаблоныАнализов",
    "Планы (OData)": "/erp_24/odata/standard.odata/Document_ПланыАнализов",
}

# HTTP-сервис endpoint'ы (как в документации)
HS_ENDPOINTS = {
    "Показатели (HTTP-сервис)": "/erp_24/hs/labindicators/indicators",
    "Шаблоны (HTTP-сервис)": "/erp_24/hs/labindicators/templates",
    "Планы (HTTP-сервис)": "/erp_24/hs/labindicators/plans",
}

# Альтернативные OData endpoint'ы (часто встречаются в 1С)
ALT_ODATA = {
    "Показатели (OData alt)": "/erp_24/odata/standard.odata/InformationRegister_Показатели",
    "Показатели (OData alt2)": "/erp_24/odata/standard.odata/Catalog_Номенклатура",
}


def print_result(name: str, success: bool, detail: str = ""):
    status = "✅" if success else "❌"
    print(f"  {status} {name}")
    if detail:
        print(f"     {detail}")


async def test_endpoint(client, name: str, url: str) -> bool:
    """Проверить один endpoint."""
    try:
        resp = await client.get(url, timeout=15)
        ok = resp.status_code == 200
        detail = f"HTTP {resp.status_code}"
        
        if ok:
            try:
                data = resp.json()
                if isinstance(data, list):
                    detail += f", массив из {len(data)} записей"
                    if data:
                        detail += f", первая: {json.dumps(data[0], ensure_ascii=False)[:150]}"
                elif isinstance(data, dict):
                    if "value" in data:
                        detail += f", OData value: {len(data['value'])} записей"
                        if data["value"]:
                            detail += f", первая: {json.dumps(data['value'][0], ensure_ascii=False)[:150]}"
                    else:
                        detail += f", dict keys: {list(data.keys())[:5]}"
            except:
                detail += f", тело: {resp.text[:100]}"
        else:
            detail += f", тело: {resp.text[:200]}"
        
        print_result(name, ok, detail)
        return ok
    except Exception as e:
        print_result(name, False, str(e)[:200])
        return False


async def main():
    print("=" * 70)
    print("🔌 ТЕСТ ПОДКЛЮЧЕНИЯ К 1С ПО ODATA")
    print("=" * 70)
    
    REAL_USER = os.environ.get("REAL_1C_USER", "")
    REAL_PASS = os.environ.get("REAL_1C_PASS", "")
    
    if not REAL_USER or not REAL_PASS:
        print("\n❌ Ошибка: не указаны credentials")
        print("   Запустите: REAL_1C_USER=логин REAL_1C_PASS=пароль python test_1c_odata.py")
        return
    
    # Маскируем пароль в выводе
    masked_pass = REAL_PASS[:2] + "***" + REAL_PASS[-1:] if len(REAL_PASS) > 3 else "***"
    print(f"\nПользователь: {REAL_USER}")
    print(f"Пароль: {masked_pass}")
    print(f"Сервер: {REAL_1C_URL}")
    
    # Basic Auth
    credentials = base64.b64encode(f"{REAL_USER}:{REAL_PASS}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    
    print("\n" + "=" * 70)
    print("📡 ТЕСТ 1: HTTP-сервисы (/hs/) — как в документации")
    print("=" * 70)
    
    async with httpx.AsyncClient(verify=False, timeout=15, headers=headers) as client:
        hs_ok = True
        for name, path in HS_ENDPOINTS.items():
            ok = await test_endpoint(client, name, f"{REAL_1C_URL}{path}")
            if not ok:
                hs_ok = False
        
        print("\n" + "=" * 70)
        print("📡 ТЕСТ 2: OData-сервисы (/odata/)")
        print("=" * 70)
        
        odata_ok = True
        for name, path in ODATA_ENDPOINTS.items():
            ok = await test_endpoint(client, name, f"{REAL_1C_URL}{path}")
            if not ok:
                odata_ok = False
        
        print("\n" + "=" * 70)
        print("📡 ТЕСТ 3: Альтернативные OData endpoint'ы")
        print("=" * 70)
        
        alt_ok = True
        for name, path in ALT_ODATA.items():
            ok = await test_endpoint(client, name, f"{REAL_1C_URL}{path}")
            if not ok:
                alt_ok = False
    
    # Итоги
    print("\n" + "=" * 70)
    print("📊 ИТОГИ")
    print("=" * 70)
    print(f"  {'✅' if hs_ok else '❌'} HTTP-сервисы (/hs/)")
    print(f"  {'✅' if odata_ok else '❌'} OData-сервисы (/odata/)")
    print(f"  {'✅' if alt_ok else '❌'} Альтернативные OData")
    
    if hs_ok:
        print("\n🎉 HTTP-сервисы работают! Интеграция готова к использованию.")
        print("   Используйте endpoint'ы из документации 1C_INDICATORS_EXPORT.md")
    elif odata_ok:
        print("\n🎉 OData работает! Нужно обновить endpoint'ы в коде.")
    else:
        print("\n❌ Ни один endpoint не ответил 200.")
        print("   Возможные причины:")
        print("   • Неправильный логин/пароль")
        print("   • Неправильный путь к сервису 1С")
        print("   • 1С использует другой тип аутентификации (NTLM, сертификаты)")
        print("   • Сервис опубликован на другом URL")


if __name__ == "__main__":
    import httpx
    asyncio.run(main())