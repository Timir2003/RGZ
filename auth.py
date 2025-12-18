from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

login_manager = LoginManager()
login_manager.login_view = 'login_page'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def register_user(username, password, subscription_level='basic', account_status='active'):
    if User.query.filter_by(username=username).first():
        return False, 'Пользователь уже существует'
    hashed_password = generate_password_hash(password)
    new_user = User(
        username=username,
        password=hashed_password,
        subscription_level=subscription_level,
        account_status=account_status
    )
    db.session.add(new_user)
    db.session.commit()
    return True, 'Пользователь создан'

def login_user_logic(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        if user.account_status == 'frozen':
            return False, 'Аккаунт заморожен'
        login_user(user)
        return True, 'Успешный вход'
    return False, 'Неверный логин или пароль'