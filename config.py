import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'student_secret_key_123')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///abac.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False