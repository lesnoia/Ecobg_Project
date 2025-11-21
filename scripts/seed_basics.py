"""Сидинг базовых данных: роли и категории."""
from backend.app import create_app, db  # type: ignore
from backend.app.models import Role, Category  # type: ignore


def main():
    app = create_app()
    with app.app_context():
        Role.get_or_create("admin", "Администратор", level=100)
        Role.get_or_create("manager", "Менеджер", level=50)
        Role.get_or_create("client", "Клиент", level=10)
        Category.seed_defaults()
        print("[OK] Роли и категории засеяны.")


if __name__ == "__main__":
    main()
