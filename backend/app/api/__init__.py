"""REST API Blueprint для ЭкоБарахолка.
Возвращает JSON для клиентских приложений (веб/десктоп PySide6).
"""
from flask import Blueprint

bp = Blueprint("api", __name__, url_prefix="/api")

from . import routes  # noqa: E402,F401
