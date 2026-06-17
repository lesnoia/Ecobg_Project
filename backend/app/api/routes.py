"""Простые REST-эндпоинты для клиента PySide6 и интеграций.
В продакшне следует добавить пагинацию, схемы валидации, аутентификацию по токену.
"""
from http import HTTPStatus
from flask import jsonify, request
from flask_login import login_required, current_user

from .. import db
from . import bp
from ..models import Category, Item


def _item_to_json(item: Item) -> dict:
    return item.to_dict()


@bp.get("/categories")
def api_categories():
    categories = Category.query.order_by(Category.name).all()
    return jsonify([{"id": c.id, "name": c.name, "description": c.description} for c in categories])


@bp.get("/items")
@login_required
def api_items_list():
    # Простые фильтры: category_id, status
    q = Item.query
    category_id = request.args.get("category_id", type=int)
    status = request.args.get("status")
    if category_id:
        q = q.filter_by(category_id=category_id)
    if status:
        q = q.filter_by(status=status)
    items = q.order_by(Item.created_at.desc()).limit(100).all()
    return jsonify([_item_to_json(i) for i in items])


@bp.post("/items")
@login_required
def api_items_create():
    data = request.get_json(silent=True) or {}
    required = ["title", "description", "category_id", "condition"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": f"Отсутствуют поля: {', '.join(missing)}"}), HTTPStatus.BAD_REQUEST

    item = Item(
        title=data["title"],
        description=data["description"],
        category_id=int(data["category_id"]),
        condition=data.get("condition", "used"),
        price=data.get("price"),
        is_free=bool(data.get("is_free")),
        is_exchangeable=bool(data.get("is_exchangeable")),
        owner_id=current_user.id,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(_item_to_json(item)), HTTPStatus.CREATED
