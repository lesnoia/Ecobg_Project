"""Одноразовая инициализация схемы БД через SQLAlchemy create_all.
Используйте, если Alembic не сгенерировал первую миграцию.
"""
from backend.app import create_app, db  # type: ignore


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("[OK] Таблицы созданы через create_all().")


if __name__ == "__main__":
    main()
