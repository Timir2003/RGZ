from flask import Flask, render_template, request, jsonify
from flask_login import login_required, current_user, logout_user
from config import Config
from models import db, User, Resource, Policy
from auth import login_manager, register_user, login_user_logic
from abac_logic import check_access
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)

# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
with app.app_context():
    db.create_all()
    # Добавляем тестовые политики
    if Policy.query.count() == 0:
        policies = [
            Policy(name='Премиум доступ', attribute='subscription_level', operator='==', value='premium', resource_id=None),
            Policy(name='Активный аккаунт', attribute='account_status', operator='==', value='active', resource_id=None),
        ]
        
        db.session.add_all(policies)
        db.session.commit()

    # Добавляем тестовые материалы
    if Resource.query.count() == 0:
        test_resources = [
            Resource(name='Python Basics', description='Основы Python', access_level='basic', available_hours='09:00-18:00'),
            Resource(name='Flask Advanced', description='Продвинутый Flask', access_level='premium', available_hours='00:00-23:59'),
            Resource(name='SQL Database', description='База данных', access_level='basic', available_hours='09:00-20:00'),
        ]
        db.session.add_all(test_resources)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/resources')
@login_required
def resources_page():
    return render_template('resources.html')

@app.route('/resource/<int:resource_id>')
@login_required
def resource_detail_page(resource_id):
    return render_template('resource_detail.html', resource_id=resource_id)

@app.route('/add-resource')
@login_required
def add_resource_page():
    if current_user.subscription_level != 'premium':
        return "Только premium пользователи могут добавлять материалы", 403
    return render_template('add_resource.html')

# API ЭНДПОИНТЫ

# Регистрация
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    subscription_level = data.get('subscription_level', 'basic')
    account_status = data.get('account_status', 'active')
    
    success, message = register_user(username, password, subscription_level, account_status)
    return jsonify({'success': success, 'message': message})

# Вход
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    success, message = login_user_logic(username, password)
    return jsonify({'success': success, 'message': message})

# Проверка авторизации
@app.route('/api/check', methods=['GET'])
def api_check():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'username': current_user.username,
            'subscription_level': current_user.subscription_level
        })
    return jsonify({'authenticated': False})

# Выход
@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'success': True, 'message': 'Вы вышли'})

# Добавление ресурса
@app.route('/api/resources', methods=['POST'])
@login_required
def api_add_resource():
    if current_user.subscription_level != 'premium':
        return jsonify({'success': False, 'message': 'Требуется premium подписка'}), 403
    
    data = request.json
    new_resource = Resource(
        name=data.get('name'),
        description=data.get('description', ''),
        access_level=data.get('access_level', 'basic'),
        available_hours=data.get('available_hours', '09:00-18:00')
    )
    db.session.add(new_resource)
    db.session.commit()
    return jsonify({'success': True, 'resource_id': new_resource.id})

# Получение всех ресурсов
@app.route('/api/resources', methods=['GET'])
@login_required
def api_get_resources():
    print(f"\n=== ЗАПРОС МАТЕРИАЛОВ ===")
    print(f"Пользователь: {current_user.username}")
    print(f"Подписка: {current_user.subscription_level}")
    print(f"Статус: {current_user.account_status}")
    print(f"Текущее время: {datetime.now().strftime('%H:%M')}")
    
    resources = Resource.query.all()
    accessible_resources = []
    
    for resource in resources:
        print(f"\nМатериал: {resource.name}")
        print(f"  Уровень: {resource.access_level}")
        print(f"  Время доступа: {resource.available_hours}")
        
        allowed, message = check_access(current_user, resource, request.remote_addr)
        print(f"  Доступ: {allowed} ({message})")
        
        if allowed:
            accessible_resources.append({
                'id': resource.id,
                'name': resource.name,
                'description': resource.description,
                'access_level': resource.access_level,
                'available_hours': resource.available_hours
            })
    
    print(f"\nИтого доступно: {len(accessible_resources)} материалов")
    return jsonify({'resources': accessible_resources})

# Получение конкретного ресурса
@app.route('/api/resources/<int:resource_id>', methods=['GET'])
@login_required
def api_get_resource(resource_id):
    print(f"Запрос ресурса {resource_id} от пользователя {current_user.username}")
    
    resource = Resource.query.get(resource_id)
    if not resource:
        print(f"Ресурс {resource_id} не найден")
        return jsonify({'success': False, 'message': 'Ресурс не найден'}), 404
    
    allowed, message = check_access(current_user, resource, request.remote_addr)
    print(f"✓ Проверка доступа: allowed={allowed}, message={message}")
    
    if not allowed:
        return jsonify({'success': False, 'message': message}), 403
    
    return jsonify({
        'success': True,
        'id': resource.id,
        'name': resource.name,
        'description': resource.description,
        'access_level': resource.access_level,
        'available_hours': resource.available_hours
    })

# Добавление политики (для админов)
@app.route('/api/policies', methods=['POST'])
@login_required
def api_add_policy():
    if current_user.subscription_level != 'premium':
        return jsonify({'success': False, 'message': 'Требуется premium'}), 403
    
    data = request.json
    new_policy = Policy(
        name=data.get('name'),
        attribute=data.get('attribute'),
        operator=data.get('operator'),
        value=data.get('value'),
        resource_id=data.get('resource_id')
    )
    db.session.add(new_policy)
    db.session.commit()
    return jsonify({'success': True, 'policy_id': new_policy.id})

if __name__ == '__main__':
    app.run(debug=True)