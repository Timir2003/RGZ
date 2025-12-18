#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def print_response(name, response):
    """Красиво печатает ответ"""
    print(f"\n{'='*60}")
    print(f"{name}")
    print(f"URL: {response.url}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        try:
            print(f"JSON: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except:
            pass
    print("="*60)

def test_api():
    """Выполняет все тестовые запросы"""
    
    # Проверка сервера
    print("Проверка сервера...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print_response("Главная страница", response)
    except:
        print("Сервер не запущен! Запустите: python app.py")
        return
    
    # Регистрация Basic пользователя
    print("\n1. Регистрация Basic пользователя")
    data = {
        "username": "student_basic",
        "password": "student123",
        "subscription_level": "basic",
        "account_status": "active"
    }
    response = requests.post(f"{BASE_URL}/api/register", json=data)
    print_response("Регистрация Basic", response)
    
    # Регистрация Premium пользователя
    print("\n2. Регистрация Premium пользователя")
    data = {
        "username": "student_premium",
        "password": "student123",
        "subscription_level": "premium",
        "account_status": "active"
    }
    response = requests.post(f"{BASE_URL}/api/register", json=data)
    print_response("Регистрация Premium", response)
    
    # Вход Basic пользователя
    print("\n3. Вход Basic пользователя")
    data = {
        "username": "student_basic",
        "password": "student123"
    }
    response = requests.post(f"{BASE_URL}/api/login", json=data)
    print_response("Вход Basic", response)
    basic_cookies = response.cookies
    
    # Вход Premium пользователя
    print("\n4. Вход Premium пользователя")
    data = {
        "username": "student_premium",
        "password": "student123"
    }
    response = requests.post(f"{BASE_URL}/api/login", json=data)
    print_response("Вход Premium", response)
    premium_cookies = response.cookies
    
    # Добавление материала (только Premium может)
    print("\n5. Добавление нового материала (Premium только)")
    
    # Premium добавляет
    data = {
        "name": "Секретный Premium курс",
        "description": "Только для избранных",
        "access_level": "premium",
        "available_hours": "00:00-23:59"
    }
    response = requests.post(f"{BASE_URL}/api/resources", 
                            json=data, 
                            cookies=premium_cookies)
    print_response("Premium добавляет материал", response)
    
    # Basic пытается добавить (должна быть ошибка)
    data = {
        "name": "Курс от Basic",
        "description": "Не должен добавиться",
        "access_level": "basic",
        "available_hours": "09:00-18:00"
    }
    response = requests.post(f"{BASE_URL}/api/resources", 
                            json=data, 
                            cookies=basic_cookies)
    print_response("Basic пытается добавить (ожидаем 403)", response)
    
    # Получение материалов для Basic
    print("\n6. Какие материалы видит Basic пользователь")
    response = requests.get(f"{BASE_URL}/api/resources", 
                          cookies=basic_cookies)
    print_response("Материалы для Basic", response)
    
    # Получение материалов для Premium
    print("\n7. Какие материалы видит Premium пользователь")
    response = requests.get(f"{BASE_URL}/api/resources", 
                          cookies=premium_cookies)
    print_response("Материалы для Premium", response)
    
    # Проверка конкретного материала
    print("\n8. Проверка доступа к конкретному материалу")
    
    # Premium пытается получить Premium материал
    response = requests.get(f"{BASE_URL}/api/resources/1", 
                          cookies=premium_cookies)
    print_response("Premium получает Premium материал", response)
    
    # Basic пытается получить тот же материал (должна быть ошибка)
    response = requests.get(f"{BASE_URL}/api/resources/1", 
                          cookies=basic_cookies)
    print_response("Basic пытается получить Premium материал", response)
    
    # Проверка авторизации
    print("\n9. Проверка текущего пользователя")
    
    response = requests.get(f"{BASE_URL}/api/check", 
                          cookies=basic_cookies)
    print_response("Кто я (Basic)", response)
    
    response = requests.get(f"{BASE_URL}/api/check", 
                          cookies=premium_cookies)
    print_response("Кто я (Premium)", response)
    
    # Выход
    print("\n10. Выход из системы")
    
    response = requests.post(f"{BASE_URL}/api/logout", 
                           cookies=basic_cookies)
    print_response("Выход Basic", response)
    
    response = requests.post(f"{BASE_URL}/api/logout", 
                           cookies=premium_cookies)
    print_response("Выход Premium", response)
    
    # Проверка после выхода
    print("\n11. Проверка доступа после выхода")
    response = requests.get(f"{BASE_URL}/api/resources")
    print_response("Доступ без авторизации (ожидаем 401)", response)

def test_abac_scenarios():
    """Тестирование ABAC сценариев"""
    print("\nТЕСТИРОВАНИЕ ABAC СЦЕНАРИЕВ")
    
    # Создаём пользователя с frozen аккаунтом
    print("\n1. Пользователь с frozen аккаунтом")
    data = {
        "username": "frozen_user",
        "password": "student123",
        "subscription_level": "premium",
        "account_status": "frozen"
    }
    response = requests.post(f"{BASE_URL}/api/register", json=data)
    print_response("Регистрация frozen пользователя", response)
    
    # Вход
    data = {"username": "frozen_user", "password": "student123"}
    response = requests.post(f"{BASE_URL}/api/login", json=data)
    print_response("Вход frozen пользователя", response)
    frozen_cookies = response.cookies
    
    # Попытка получить материалы
    response = requests.get(f"{BASE_URL}/api/resources", 
                          cookies=frozen_cookies)
    print_response("Frozen пользователь пытается получить материалы", response)
    
    # 2. Материал с ограничением по времени
    print("\n2. Материал с ограничением по времени")
    
    # Сначала добавим материал (через нового premium пользователя)
    premium_data = {
        "username": "test_premium",
        "password": "test123",
        "subscription_level": "premium",
        "account_status": "active"
    }
    requests.post(f"{BASE_URL}/api/register", json=premium_data)
    
    login_res = requests.post(f"{BASE_URL}/api/login", 
                             json={"username": "test_premium", "password": "test123"})
    premium_cookies = login_res.cookies
    
    # Добавляем материал доступный только утром
    data = {
        "name": "Утренний курс (только 03:00-05:00)",
        "description": "Доступен только глубокой ночью",
        "access_level": "basic",
        "available_hours": "03:00-05:00"
    }
    response = requests.post(f"{BASE_URL}/api/resources", 
                            json=data, 
                            cookies=premium_cookies)
    print_response("Добавлен материал с ограничением по времени", response)
    
    # Basic пользователь пытается получить
    basic_data = {
        "username": "test_basic",
        "password": "test123",
        "subscription_level": "basic",
        "account_status": "active"
    }
    requests.post(f"{BASE_URL}/api/register", json=basic_data)
    login_res = requests.post(f"{BASE_URL}/api/login", 
                             json={"username": "test_basic", "password": "test123"})
    basic_cookies = login_res.cookies
    
    response = requests.get(f"{BASE_URL}/api/resources", 
                          cookies=basic_cookies)
    
    print("\nРезультаты ABAC проверки:")
    materials = response.json().get('resources', [])
    for material in materials:
        if "Утренний курс" in material['name']:
            print(f"Материал '{material['name']}' НЕ доступен (вне времени)")
        else:
            print(f"Материал '{material['name']}' доступен")