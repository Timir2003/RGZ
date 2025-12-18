import pytest
from app import app, db
from models import User

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
    data = response.get_json()
    assert data['success'] == True

def test_login(client):

    client.post('/api/register', json={'username': 'test', 'password': 'test'})
    
    response = client.post('/api/login', json={'username': 'test', 'password': 'test'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] == True