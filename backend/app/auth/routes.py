"""Маршруты аутентификации."""
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse

from .. import db
from . import bp
from .forms import LoginForm, RegistrationForm
from ..models import Role, User, UserRole


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Вход пользователя."""

    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Неверное имя пользователя или пароль", "danger")
            return redirect(url_for("auth.login"))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("main.dashboard")
        return redirect(next_page)

    return render_template("auth/login.html", title="Вход", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Регистрация пользователя."""

    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Назначаем роль клиента по умолчанию
        client_role = Role.get_or_create("client", "Клиент платформы", level=10)
        db.session.add(UserRole(user_id=user.id, role_id=client_role.id))
        # Если ещё нет ни одного администратора — делаем первого пользователя администратором
        admin_role = Role.get_or_create("admin", "Администратор", level=100)
        has_admin = (
            UserRole.query.filter_by(role_id=admin_role.id).first() is not None
        )
        if not has_admin:
            db.session.add(UserRole(user_id=user.id, role_id=admin_role.id))
        db.session.commit()

        if not has_admin:
            flash(
                "Поздравляем! Вы успешно зарегистрировались и стали администратором (первый пользователь).",
                "success",
            )
        else:
            flash("Поздравляем! Вы успешно зарегистрировались.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", title="Регистрация", form=form)


@bp.route("/logout")
@login_required
def logout():
    """Выход пользователя."""

    logout_user()
    flash("Вы вышли из системы", "info")
    return redirect(url_for("auth.login"))
