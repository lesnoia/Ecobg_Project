"""Основной Blueprint приложения."""
from flask import Blueprint

bp = Blueprint("main", __name__)

from . import main  # noqa: E402,F401
