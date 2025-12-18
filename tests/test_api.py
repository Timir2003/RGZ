import pytest
from app import app, db
from models import User, Resource

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
        with app.app_context():
            db.drop_all()

def test_register(client):
    response = client.post('/api/register', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 200
    assert b'Пользователь создан' in response.data

def test_login(client):
    client.post('/api/register', json={'username': 'test', 'password': 'test'})
    response = client.post('/api/login', json={'username': 'test', 'password': 'test'})
    assert response.status_code == 200
    assert b'Успешный вход' in response.data

def test_access_denied(client):
    # Регистрируем basic пользователя
    client.post('/api/register', json={'username': 'basic', 'password': 'pass', 'subscription_level': 'basic'})
    client.post('/api/login', json={'username': 'basic', 'password': 'pass'})
    
    # Создаем premium ресурс (через прямое добавление в БД)
    with app.app_context():
        resource = Resource(name='Premium Course', access_level='premium')
        db.session.add(resource)
        db.session.commit()
        resource_id = resource.id
    
    response = client.get(f'/api/resources/{resource_id}')
    assert response.status_code == 403
    assert b'Требуется subscription_level = premium' in response.data