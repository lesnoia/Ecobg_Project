# Архитектура «MUIVesg»

## Слои системы
- API-слой: Flask Blueprints (`backend/app/api`, `backend/app/routes`) — REST JSON и серверные HTML-представления.
- Сервисный слой: `backend/services` — бизнес-логика (будет наполнен).
- Слой доступа к данным (DAL): `backend/repositories` — работа с ORM (будет наполнен).
- ORM-модели: `backend/app/models.py` — SQLAlchemy.
- GUI-клиент: PySide6 (`client/…`) — 10+ окон/диалогов (будет реализовано).
- Миграции/БД: `backend/db` — Alembic/Flask-Migrate (будет наполнен), `data/` — дампы/тестовые данные.

## Стек
- Python 3.10+, Flask, SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF
- PostgreSQL (psycopg2-binary)
- PySide6
- Документы: python-docx, openpyxl

## Модель данных (кратко)
- Пользователи/роли: `users`, `roles`, `user_roles`
- Каталоги: `categories`, `hazard_classes`, `recycling_methods`
- Объявления и файлы: `items`, `item_documents`
- Сделки/операции: `exchange_requests`, `donations`, `recycling_operations`, `disposal_requests`
- Системные: `activity_logs`, `notifications`, `system_settings`

(План: унифицировать сделки через `deals`/`deal_items`, добавить `messages`).

## Эндпоинты (минимум)
- GET /api/categories — список категорий
- GET /api/items — список объявлений (фильтры)
- POST /api/items — создать объявление

## Диаграмма модулей (описательно)
- `backend/app/__init__.py` — фабрика приложения, регистрация блюпринтов
- `backend/app/models.py` — ORM-модели и вспомогательные методы
- `backend/app/routes/` — серверные HTML-маршруты
- `backend/app/api/` — REST-эндпоинты
- `backend/app/auth/` — аутентификация, формы
