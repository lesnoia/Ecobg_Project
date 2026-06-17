"""Формы аутентификации и регистрации."""
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from ..models import User


class LoginForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class RegistrationForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[DataRequired(), Length(min=3, max=64)],
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    full_name = StringField("ФИО", validators=[Length(max=120)])
    phone = StringField("Телефон", validators=[Length(max=32)])
    password = PasswordField(
        "Пароль",
        validators=[DataRequired(), Length(min=6)],
    )
    confirm_password = PasswordField(
        "Повторите пароль",
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = SubmitField("Зарегистрироваться")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Такое имя пользователя уже занято")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Такой email уже зарегистрирован")
