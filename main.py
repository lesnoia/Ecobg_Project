"""Точка входа в приложение MUIVesg.

Этот модуль запускает серверную часть (Flask API),
Для разработки используется переменная окружения FLASK_ENV и файл .env с секретами.
"""
from backend.app import create_app

app = create_app()


if __name__ == "__main__":
    # Включаем режим разработки при прямом запуске
    app.run(debug=True)
