"""Маршруты основной части приложения."""
from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .. import db
from ..forms import (
    DonationForm,
    ExchangeRequestForm,
    HelpTextForm,
    ItemForm,
    RecyclingForm,
)
from ..models import (
    Category,
    Donation,
    ExchangeRequest,
    User,
    UserRole,
    Item,
    Role,
    RecyclingOperation,
    SystemSetting,
)
from . import bp


@bp.route("/")
def index():
    """Главная страница с подборкой объявлений."""

    items = Item.query.order_by(Item.created_at.desc()).limit(12).all()
    return render_template("main/index.html", items=items, title="ShelterShare")


@bp.route("/dashboard")
@login_required
def dashboard():
    """Панель пользователя."""

    items = Item.query.filter_by(owner_id=current_user.id).all()
    exchange_requests = ExchangeRequest.query.filter_by(requester_id=current_user.id).all()
    donations = Donation.query.filter_by(donor_id=current_user.id).all()
    return render_template(
        "main/dashboard.html",
        title="Личный кабинет",
        items=items,
        exchange_requests=exchange_requests,
        donations=donations,
    )


@bp.route("/items")
def items_list():
    """Список объявлений с фильтрами и сортировкой."""

    query = Item.query
    category_id = request.args.get("category", type=int)
    status = request.args.get("status")
    sort = request.args.get("sort", default="date_desc")

    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        query = query.filter_by(status=status)

    if sort == "price_asc":
        # MySQL не поддерживает NULLS LAST — эмулируем: сначала не-NULL, затем NULL
        query = query.order_by(Item.price.is_(None), Item.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Item.price.is_(None), Item.price.desc())
    else:
        query = query.order_by(Item.created_at.desc())

    categories = Category.query.all()
    items = query.all()
    return render_template(
        "main/items.html",
        title="Объявления",
        items=items,
        categories=categories,
        selected_category=category_id,
        selected_status=status,
        selected_sort=sort,
    )


@bp.route("/items/<int:item_id>")
def item_detail(item_id: int):
    """Карточка объявления."""

    item = Item.query.get_or_404(item_id)

    recycling_form = RecyclingForm(prefix="recycle")
    exchange_form = ExchangeRequestForm(prefix="exchange")
    donation_form = DonationForm(prefix="donate")

    if current_user.is_authenticated:
        exchange_form.offered_item_id.choices = [
            (usr_item.id, usr_item.title)
            for usr_item in Item.query.filter_by(owner_id=current_user.id).all()
        ]
    else:
        exchange_form.offered_item_id.choices = []

    # Входящие заявки на этот товар (для владельца)
    incoming = []
    if current_user.is_authenticated and current_user.id == item.owner_id:
        incoming = [r for r in item.incoming_requests if r.status == "pending"]

    return render_template(
        "main/item_detail.html",
        title=item.title,
        item=item,
        recycling_form=recycling_form,
        exchange_form=exchange_form,
        donation_form=donation_form,
        incoming_requests=incoming,
    )


@bp.route("/requests/<int:req_id>/accept", methods=["POST"])
@login_required
def accept_request(req_id: int):
    """Подтвердить заявку владельцем вещи (покупка или обмен)."""

    req = ExchangeRequest.query.get_or_404(req_id)
    item = Item.query.get_or_404(req.target_item_id)
    if item.owner_id != current_user.id:
        abort(403)
    if req.status != "pending":
        flash("Заявка уже обработана", "info")
        return redirect(url_for("main.item_detail", item_id=item.id))

    req.status = "accepted"
    # Покупка: нет предложенной вещи — закрепляем продажу
    if req.offered_item_id is None:
        item.status = "sold"
        # Передаём право собственности покупателю
        item.owner_id = req.requester_id
        # Отклоняем остальные заявки на этот товар
        for other in ExchangeRequest.query.filter(
            ExchangeRequest.target_item_id == item.id,
            ExchangeRequest.id != req.id,
            ExchangeRequest.status == "pending",
        ).all():
            other.status = "declined"
    else:
        # Обмен: помечаем обе вещи зарезервированными
        item.status = "reserved"
        offered = Item.query.get(req.offered_item_id)
        if offered:
            offered.status = "reserved"
    db.session.commit()
    flash("Заявка подтверждена", "success")
    return redirect(url_for("main.item_detail", item_id=item.id))


@bp.route("/requests/<int:req_id>/decline", methods=["POST"])
@login_required
def decline_request(req_id: int):
    """Отклонить заявку владельцем вещи."""

    req = ExchangeRequest.query.get_or_404(req_id)
    item = Item.query.get_or_404(req.target_item_id)
    if item.owner_id != current_user.id:
        abort(403)
    if req.status != "pending":
        flash("Заявка уже обработана", "info")
        return redirect(url_for("main.item_detail", item_id=item.id))

    req.status = "declined"
    db.session.commit()
    flash("Заявка отклонена", "success")
    return redirect(url_for("main.item_detail", item_id=item.id))


@bp.route("/items/create", methods=["GET", "POST"])
@login_required
def create_item():
    """Создание нового объявления (упрощённая версия)."""

    form = ItemForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        item = Item(
            title=form.title.data,
            description=form.description.data,
            category_id=form.category_id.data,
            condition=form.condition.data,
            price=form.price.data,
            is_free=form.is_free.data,
            is_exchangeable=form.is_exchangeable.data,
            owner_id=current_user.id,
        )
        db.session.add(item)
        db.session.commit()
        flash("Объявление опубликовано", "success")
        return redirect(url_for("main.item_detail", item_id=item.id))
    # Показ формы при первом заходе или при невалидной отправке
    return render_template("main/item_form.html", title="Новое объявление", form=form)

@bp.route("/items/<int:item_id>/buy", methods=["POST"])
@login_required
def buy_item(item_id: int):
    """Простой сценарий покупки: пометить объявление как зарезервированное покупателем.
    В дальнейшем можно расширить до полноценной сущности сделки.
    """

    item = Item.query.get_or_404(item_id)
    if item.owner_id == current_user.id:
        flash("Нельзя купить собственную вещь", "warning")
        return redirect(url_for("main.item_detail", item_id=item.id))
    if item.status != "available":
        flash("Вещь недоступна для покупки", "warning")
        return redirect(url_for("main.item_detail", item_id=item.id))
    if not item.price or item.is_free:
        flash("Для покупки должна быть указана цена", "warning")
        return redirect(url_for("main.item_detail", item_id=item.id))

    # Создаём заявку как ExchangeRequest без предложенной вещи
    req = ExchangeRequest(
        requester_id=current_user.id,
        target_item_id=item.id,
        offered_item_id=None,
        message="Заявка на покупку",
        status="pending",
    )
    db.session.add(req)
    db.session.commit()
    flash("Запрос на покупку отправлен. Ожидайте подтверждения владельца.", "success")
    return redirect(url_for("main.item_detail", item_id=item.id))


@bp.route("/recycling/<int:item_id>", methods=["POST"])
@login_required
def mark_recycled(item_id: int):
    """Отметить вещь переработанной."""

    item = Item.query.get_or_404(item_id)
    form = RecyclingForm(prefix="recycle")
    if form.validate_on_submit():
        operation = RecyclingOperation(
            item_id=item.id,
            operator_id=current_user.id,
            method=form.method.data,
            location=form.location.data,
            notes=form.notes.data,
        )
        item.status = "recycled"
        db.session.add(operation)
        db.session.commit()
        flash("Информация о переработке сохранена", "success")
    else:
        flash("Проверьте правильность данных по переработке", "warning")
    return redirect(url_for("main.item_detail", item_id=item.id))


@bp.route("/items/<int:item_id>/exchange", methods=["POST"])
@login_required
def request_exchange(item_id: int):
    """Создать заявку на обмен."""

    item = Item.query.get_or_404(item_id)
    form = ExchangeRequestForm(prefix="exchange")
    form.offered_item_id.choices = [
        (usr_item.id, usr_item.title)
        for usr_item in Item.query.filter_by(owner_id=current_user.id).all()
    ]
    if form.validate_on_submit():
        exchange = ExchangeRequest(
            requester_id=current_user.id,
            target_item_id=item.id,
            offered_item_id=form.offered_item_id.data,
            message=form.message.data,
        )
        db.session.add(exchange)
        db.session.commit()
        flash("Заявка на обмен отправлена", "success")
    else:
        flash("Не удалось отправить заявку", "warning")
    return redirect(url_for("main.item_detail", item_id=item.id))


@bp.route("/items/<int:item_id>/donate", methods=["POST"])
@login_required
def donate_item(item_id: int):
    """Подтвердить передачу вещи в дар."""

    item = Item.query.get_or_404(item_id)
    if item.owner_id != current_user.id:
        abort(403)
    form = DonationForm(prefix="donate")
    if form.validate_on_submit():
        donation = Donation(
            item_id=item.id,
            donor_id=current_user.id,
            status="confirmed",
            confirmation_doc=form.notes.data,
        )
        item.status = "donated"
        db.session.add(donation)
        db.session.commit()
        flash("Пожертвование зафиксировано", "success")
    else:
        flash("Не удалось сохранить пожертвование", "warning")
    return redirect(url_for("main.item_detail", item_id=item.id))


@bp.route("/help")
def help_page():
    """Справка по системе."""

    info = SystemSetting.query.filter_by(key="help_text").first()
    return render_template("main/help.html", title="Справка", info=info)


@bp.route("/admin/help", methods=["GET", "POST"])
@login_required
def edit_help():
    """Редактирование справки (только для администраторов)."""

    if not current_user.has_role("admin"):
        abort(403)
    record = SystemSetting.query.filter_by(key="help_text").first()
    form = HelpTextForm()
    if record and request.method == "GET":
        form.body.data = record.value
    if form.validate_on_submit():
        if not record:
            record = SystemSetting(key="help_text")
            db.session.add(record)
        record.value = form.body.data
        record.description = "Справочная информация"
        db.session.commit()
        flash("Справка обновлена", "success")
        return redirect(url_for("main.help_page"))
    return render_template("main/help_edit.html", title="Редактор справки", form=form)


@bp.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_item(item_id: int):
    """Редактирование объявления владельцем."""

    item = Item.query.get_or_404(item_id)
    if item.owner_id != current_user.id:
        abort(403)
    form = ItemForm(obj=item)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        item.title = form.title.data
        item.description = form.description.data
        item.category_id = form.category_id.data
        item.condition = form.condition.data
        item.price = form.price.data
        item.is_free = form.is_free.data
        item.is_exchangeable = form.is_exchangeable.data
        db.session.commit()
        flash("Объявление обновлено", "success")
        return redirect(url_for("main.item_detail", item_id=item.id))
    return render_template("main/item_form.html", title="Редактирование объявления", form=form)


@bp.route("/items/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id: int):
    """Удаление объявления владельцем."""

    item = Item.query.get_or_404(item_id)
    if item.owner_id != current_user.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash("Объявление удалено", "success")
    return redirect(url_for("main.dashboard"))


@bp.route("/admin/seed", methods=["POST"])
@login_required
def seed_data():
    """Инициализация базовых ролей и категорий (только админ)."""

    if not current_user.has_role("admin"):
        abort(403)
    # Роли по умолчанию
    Role.get_or_create("admin", "Администратор", level=100)
    Role.get_or_create("manager", "Менеджер", level=50)
    Role.get_or_create("client", "Клиент", level=10)
    # Категории по умолчанию
    Category.seed_defaults()
    flash("Справочники инициализированы", "success")
    return redirect(url_for("main.dashboard"))


# ===== Управление ролями (веб-страница для администратора) =====
@bp.route("/admin/users", methods=["GET", "POST"])
@login_required
def admin_users():
    if not current_user.has_role("admin"):
        abort(403)

    # Выдача/снятие ролей (простая форма POST)
    if request.method == "POST":
        username = request.form.get("username")
        action = request.form.get("action")  # add/remove
        role_name = request.form.get("role")
        user = User.query.filter_by(username=username).first()
        role = Role.get_or_create(role_name)
        if not user:
            flash("Пользователь не найден", "warning")
            return redirect(url_for("main.admin_users"))
        if action == "add":
            if not any(link.role_id == role.id for link in user.roles):
                db.session.add(UserRole(user_id=user.id, role_id=role.id))
                db.session.commit()
                flash("Роль выдана", "success")
            else:
                flash("У пользователя уже есть эта роль", "info")
        elif action == "remove":
            link = next((l for l in user.roles if l.role_id == role.id), None)
            if link:
                db.session.delete(link)
                db.session.commit()
                flash("Роль снята", "success")
            else:
                flash("У пользователя нет этой роли", "info")
        return redirect(url_for("main.admin_users"))

    users = User.query.order_by(User.username).all()
    roles = Role.query.order_by(Role.name).all()
    return render_template("admin/users.html", title="Пользователи и роли", users=users, roles=roles)
