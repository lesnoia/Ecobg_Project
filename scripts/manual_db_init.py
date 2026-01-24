# !/usr/bin/env python3
print("Ручная инициализация БД...")

# Настройка путей
import sys

sys.path.extend([
    '/usr/lib/python3/dist-packages',
    '/usr/local/lib/python3.12/dist-packages',
    '/app/backend',
    '/app'
])

# Создаем минимальное Flask приложение
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Берем настройки из config.py
try:
    import config

    db_uri = config.Config.SQLALCHEMY_DATABASE_URI
    print(f"Используем URI из config: {db_uri[:50]}...")
except:
    # Или из переменных окружения Railway
    db_uri = os.environ.get('DATABASE_URL')
    if db_uri and db_uri.startswith('mysql://'):
        db_uri = db_uri.replace('mysql://', 'mysql+pymysql://', 1)
    print(f"Используем URI из окружения: {db_uri[:50]}...")

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Определяем базовые модели (упрощенные)
class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    level = db.Column(db.Integer, default=0)


# Создаем таблицы
with app.app_context():
    db.create_all()
    print("✅ Таблицы созданы")

    # Добавляем категории
    if Category.query.count() == 0:
        categories = ['Недвижимость', 'Транспорт', 'Работа', 'Услуги', 'Личные вещи']
        for name in categories:
            db.session.add(Category(name=name))
        db.session.commit()
        print(f"✅ Добавлено {len(categories)} категорий")

    # Добавляем роли
    if Role.query.count() == 0:
        roles = [
            ("admin", "Администратор", 100),
            ("manager", "Менеджер", 50),
            ("client", "Клиент", 10)
        ]
        for name, description, level in roles:
            db.session.add(Role(name=name, description=description, level=level))
        db.session.commit()
        print("✅ Роли добавлены")

    print("🎉 База данных полностью инициализирована!")
EOF