from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Пользователь
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    subscription_level = db.Column(db.String(20), default='basic')
    account_status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Ресурс (обучающий материал)
class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    access_level = db.Column(db.String(20), default='basic')
    available_hours = db.Column(db.String(50), default='09:00-18:00')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Политика доступа (ABAC правило)
class Policy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    attribute = db.Column(db.String(50), nullable=False)
    operator = db.Column(db.String(10), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)