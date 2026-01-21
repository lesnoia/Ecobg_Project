from flask import Flask
from flask import request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
migrate = Migrate()

def create_app():
    # Определяем путь к статической папке
    import os
    basedir = os.path.abspath(os.path.dirname(__file__))
    static_folder = os.path.join(basedir, 'static')
    
    app = Flask(__name__, static_folder=static_folder)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints (внутрипакетные относительные импорты)
    from .routes import bp as main_bp
    from .auth import bp as auth_bp
    from .api import bp as api_bp
    # ВАЖНО: импорт моделей, чтобы Alembic видел метаданные при автогенерации
    from . import models  # noqa: F401
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def inject_breadcrumbs():
        try:
            crumbs = [("Главная", url_for("main.index"))]
            ep = request.endpoint or ""
            if ep.startswith("main."):
                if ep == "main.items_list":
                    crumbs.append(("Объявления", url_for("main.items_list")))
                elif ep == "main.item_detail":
                    crumbs.append(("Объявления", url_for("main.items_list")))
                elif ep == "main.help_page":
                    crumbs.append(("Справка", url_for("main.help_page")))
                elif ep in {
                    "main.about","main.contacts","main.faq","main.howitworks",
                    "main.categories_page","main.news","main.partners","main.support",
                    "main.privacy","main.terms","main.feedback"
                }:
                    titles = {
                        "main.about": "О нас",
                        "main.contacts": "Контакты",
                        "main.faq": "FAQ",
                        "main.howitworks": "Как это работает",
                        "main.categories_page": "Категории",
                        "main.news": "Новости",
                        "main.partners": "Партнёрам",
                        "main.support": "Поддержка",
                        "main.privacy": "Политика",
                        "main.terms": "Условия",
                        "main.feedback": "Обратная связь",
                    }
                    url = url_for(ep)
                    crumbs.append((titles.get(ep, ep), url))
            return {"breadcrumbs": crumbs}
        except Exception:
            return {"breadcrumbs": []}

    # Автоматически создаём отсутствующие таблицы при запуске приложения
    # Это безопасно: существующие таблицы не трогаются, создаются только недостающие
    with app.app_context():
        db.create_all()
        # Создаём папку для загрузок, если её нет
        upload_folder = app.config.get('UPLOAD_FOLDER')
        if upload_folder:
            os.makedirs(upload_folder, exist_ok=True)

    return app
