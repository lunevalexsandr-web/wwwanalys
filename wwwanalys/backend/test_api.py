import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Тест проверки здоровья API"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Health check passed")
    else:
        print("✗ Health check failed")
    return response.status_code == 200

def test_user_registration():
    """Тест регистрации пользователя"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "is_active": True,
        "is_admin": False
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"User registration status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ User registration successful")
        return True
    elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
        print("✓ User already exists (this is OK for the test)")
        return True
    else:
        print("✗ User registration failed")
        return False

def test_user_login():
    """Тест входа пользователя"""
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
    print(f"User login status: {response.status_code}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✓ User login successful")
        return token
    else:
        print("✗ User login failed")
        return None

def test_create_analysis_type(token):
    """Тест создания типа анализа"""
    headers = {"Authorization": f"Bearer {token}"}
    
    analysis_type_data = {
        "name": "Тестовый анализ",
        "description": "Описание тестового анализа",
        "indicators": [
            {
                "name": "Температура",
                "unit": "°C",
                "min_value": 20.0,
                "max_value": 25.0
            },
            {
                "name": "Давление",
                "unit": "кПа",
                "min_value": 100.0,
                "max_value": 120.0
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/analysis-types/", json=analysis_type_data, headers=headers)
    print(f"Create analysis type status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Analysis type created successfully")
        return response.json()
    else:
        print("✗ Failed to create analysis type")
        print(f"Response: {response.text}")
        return None

def test_get_analysis_types(token):
    """Тест получения списка типов анализов"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/analysis-types/", headers=headers)
    print(f"Get analysis types status: {response.status_code}")
    
    if response.status_code == 200:
        analysis_types = response.json()
        print(f"✓ Retrieved {len(analysis_types)} analysis types")
        return analysis_types
    else:
        print("✗ Failed to get analysis types")
        return None

def test_create_process_log(token, analysis_type_id):
    """Тест создания записи в журнале процессов"""
    headers = {"Authorization": f"Bearer {token}"}
    
    process_log_data = {
        "analysis_type_id": analysis_type_id,
        "notes": "Тестовая запись",
        "indicator_values": [
            {
                "indicator_id": 1,  # ID первого индикатора (температура)
                "value": 22.5
            },
            {
                "indicator_id": 2,  # ID второго индикатора (давление)
                "value": 110.0
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/process-logs/", json=process_log_data, headers=headers)
    print(f"Create process log status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Process log created successfully")
        return response.json()
    else:
        print("✗ Failed to create process log")
        print(f"Response: {response.text}")
        return None

def test_get_process_logs(token):
    """Тест получения списка записей журнала"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/process-logs/", headers=headers)
    print(f"Get process logs status: {response.status_code}")
    
    if response.status_code == 200:
        process_logs = response.json()
        print(f"✓ Retrieved {len(process_logs)} process logs")
        return process_logs
    else:
        print("✗ Failed to get process logs")
        return None

def main():
    """Основная функция тестирования"""
    print("=== WWWAnalys API Testing ===\n")
    
    # Проверка доступности API
    if not test_health():
        print("API is not available. Please make sure the backend is running on http://localhost:8000")
        return
    
    # Регистрация и вход пользователя
    if not test_user_registration():
        print("Failed to register user")
        return
    
    token = test_user_login()
    if not token:
        print("Failed to login")
        return
    
    print("\n--- Testing Analysis Types ---")
    
    # Создание типа анализа
    analysis_type = test_create_analysis_type(token)
    if not analysis_type:
        print("Failed to create analysis type")
        return
    
    # Получение списка типов анализов
    analysis_types = test_get_analysis_types(token)
    if analysis_types:
        print(f"Found analysis types: {', '.join([at['name'] for at in analysis_types])}")
    
    print("\n--- Testing Process Logs ---")
    
    # Создание записи в журнале
    if analysis_type and 'id' in analysis_type:
        process_log = test_create_process_log(token, analysis_type['id'])
        if process_log:
            print(f"Created process log with ID: {process_log.get('id')}")
        
        # Получение списка записей журнала
        process_logs = test_get_process_logs(token)
        if process_logs:
            print(f"Found process logs: {len(process_logs)} total")
    
    print("\n=== Testing Complete ===")

if __name__ == "__main__":
    main()