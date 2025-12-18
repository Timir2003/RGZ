import pytest
import json
from app import app, db
from models import User, Resource, Policy
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    """Создаёт тестового клиента Flask"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Создаём тестовых пользователей
            users = [
                User(username='basic_user', 
                     password=generate_password_hash('123'), 
                     subscription_level='basic', 
                     account_status='active'),
                User(username='premium_user', 
                     password=generate_password_hash('123'), 
                     subscription_level='premium', 
                     account_status='active'),
                User(username='frozen_user', 
                     password=generate_password_hash('123'), 
                     subscription_level='premium', 
                     account_status='frozen'),
            ]
            db.session.add_all(users)
            
            # Создаём тестовые ресурсы
            resources = [
                Resource(name='Python Basics', 
                         description='Основы Python',
                         access_level='basic',
                         available_hours='00:00-23:59'),
                Resource(name='Flask Advanced', 
                         description='Продвинутый Flask',
                         access_level='premium',
                         available_hours='00:00-23:59'),
                Resource(name='Утренний курс', 
                         description='Только утром',
                         access_level='basic',
                         available_hours='09:00-12:00'),
            ]
            db.session.add_all(resources)
            
            # Создаём политики
            policies = [
                Policy(name='Premium доступ', 
                       attribute='subscription_level', 
                       operator='==', 
                       value='premium',
                       resource_id=None),
                Policy(name='Активный аккаунт', 
                       attribute='account_status', 
                       operator='==', 
                       value='active',
                       resource_id=None),
            ]
            db.session.add_all(policies)
            
            db.session.commit()
        
        yield client
        
        with app.app_context():
            db.drop_all()

# ==================== ТЕСТЫ API ====================

def test_register_user(client):
    """Тест регистрации нового пользователя"""
    response = client.post('/api/register', 
                          json={'username': 'new_user', 
                                'password': 'password123',
                                'subscription_level': 'basic',
                                'account_status': 'active'})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True

def test_login_basic_user(client):
    """Тест входа basic пользователя"""
    response = client.post('/api/login', 
                          json={'username': 'basic_user', 
                                'password': '123'})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True

def test_login_premium_user(client):
    """Тест входа premium пользователя"""
    response = client.post('/api/login', 
                          json={'username': 'premium_user', 
                                'password': '123'})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True

def test_get_resources_basic(client):
    """Тест: Basic пользователь видит только basic материалы"""
    # Сначала логинимся
    client.post('/api/login', 
               json={'username': 'basic_user', 'password': '123'})
    
    response = client.get('/api/resources')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    resources = data['resources']
    
    # Basic должен видеть только basic материалы
    for resource in resources:
        assert resource['access_level'] == 'basic'

def test_get_resources_premium(client):
    """Тест: Premium пользователь видит все материалы"""
    # Сначала логинимся
    client.post('/api/login', 
               json={'username': 'premium_user', 'password': '123'})
    
    response = client.get('/api/resources')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    resources = data['resources']
    
    # Premium должен видеть и basic, и premium
    access_levels = [r['access_level'] for r in resources]
    assert 'basic' in access_levels
    assert 'premium' in access_levels

def test_access_denied_for_frozen(client):
    """Тест: Frozen пользователь не имеет доступа"""
    response = client.post('/api/login', 
                          json={'username': 'frozen_user', 
                                'password': '123'})
    
    # Даже после входа доступ к материалам должен быть запрещён
    client.post('/api/login', 
               json={'username': 'frozen_user', 'password': '123'})
    
    response = client.get('/api/resources')
    # Либо 401 (не авторизован), либо 403 (запрещено)
    assert response.status_code in [401, 403]

def test_add_resource_permission(client):
    """Тест: Только premium может добавлять материалы"""
    # Premium пользователь может добавить
    client.post('/api/login', 
               json={'username': 'premium_user', 'password': '123'})
    
    response = client.post('/api/resources',
                          json={'name': 'Новый курс',
                                'access_level': 'basic',
                                'available_hours': '09:00-18:00'})
    
    assert response.status_code == 200
    
    # Basic пользователь не может добавить
    client.post('/api/login', 
               json={'username': 'basic_user', 'password': '123'})
    
    response = client.post('/api/resources',
                          json={'name': 'Курс от basic',
                                'access_level': 'basic',
                                'available_hours': '09:00-18:00'})
    
    assert response.status_code == 403  # Forbidden

def test_unauthorized_access(client):
    """Тест: Неавторизованный доступ запрещён"""
    response = client.get('/api/resources')
    assert response.status_code == 401  # Unauthorized

def test_check_auth_status(client):
    """Тест: Проверка статуса авторизации"""
    # До входа
    response = client.get('/api/check')
    data = json.loads(response.data)
    assert data['authenticated'] == False
    
    # После входа
    client.post('/api/login', 
               json={'username': 'basic_user', 'password': '123'})
    
    response = client.get('/api/check')
    data = json.loads(response.data)
    assert data['authenticated'] == True
    assert data['username'] == 'basic_user'

def test_logout(client):
    """Тест: Выход из системы"""
    # Входим
    client.post('/api/login', 
               json={'username': 'basic_user', 'password': '123'})
    
    # Проверяем что вошли
    response = client.get('/api/check')
    data = json.loads(response.data)
    assert data['authenticated'] == True
    
    # Выходим
    response = client.post('/api/logout')
    assert response.status_code == 200
    
    # Проверяем что вышли
    response = client.get('/api/check')
    data = json.loads(response.data)
    assert data['authenticated'] == False

# ==================== ТЕСТЫ ABAC ====================

def test_abac_premium_access(client):
    """Тест ABAC: Premium доступ к premium материалам"""
    client.post('/api/login', 
               json={'username': 'premium_user', 'password': '123'})
    
    # Получаем ID premium материала
    response = client.get('/api/resources')
    data = json.loads(response.data)
    
    premium_resources = [r for r in data['resources'] if r['access_level'] == 'premium']
    if premium_resources:
        resource_id = premium_resources[0]['id']
        
        # Пытаемся получить доступ
        response = client.get(f'/api/resources/{resource_id}')
        # Premium должен получить доступ
        assert response.status_code == 200

def test_abac_basic_denied_premium(client):
    """Тест ABAC: Basic доступ к premium материалам запрещён"""
    client.post('/api/login', 
               json={'username': 'basic_user', 'password': '123'})
    
    # Получаем ID premium материала
    response = client.get('/api/resources')
    data = json.loads(response.data)
    
    premium_resources = [r for r in data['resources'] if r['access_level'] == 'premium']
    if premium_resources:
        resource_id = premium_resources[0]['id']
        
        # Пытаемся получить доступ
        response = client.get(f'/api/resources/{resource_id}')
        # Basic должен получить отказ
        assert response.status_code == 403