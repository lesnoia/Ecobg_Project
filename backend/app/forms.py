"""WTForms для основных сущностей приложения."""
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DecimalField,
    HiddenField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class ItemForm(FlaskForm):
    title = StringField("Название", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Описание", validators=[DataRequired(), Length(min=20)])
    category_id = SelectField("Категория", coerce=int, validators=[DataRequired()])
    condition = SelectField(
        "Состояние",
        choices=[
            ("new", "Новое"),
            ("like_new", "Как новое"),
            ("used", "Б/У"),
            ("needs_repair", "Требует ремонта"),
        ],
        validators=[DataRequired()],
    )
    price = DecimalField(
        "Цена",
        validators=[Optional(), NumberRange(min=0)],
        places=2,
    )
    is_free = BooleanField("Отдаю бесплатно")
    is_exchangeable = BooleanField("Готов к обмену")
    submit = SubmitField("Сохранить")


class RecyclingForm(FlaskForm):
    method = StringField("Способ переработки", validators=[DataRequired(), Length(max=120)])
    location = StringField("Локация", validators=[Length(max=255)])
    notes = TextAreaField("Комментарий", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Отметить переработку")


class ExchangeRequestForm(FlaskForm):
    offered_item_id = SelectField("Предлагаемая вещь", coerce=int)
    message = TextAreaField("Сообщение", validators=[Length(max=500)])
    submit = SubmitField("Отправить заявку")


class DonationForm(FlaskForm):
    recipient_name = StringField("Получатель", validators=[Length(max=120)])
    notes = TextAreaField("Комментарий", validators=[Length(max=500)])
    submit = SubmitField("Подтвердить передачу")


class HelpTextForm(FlaskForm):
    key = HiddenField(default="help_text")
    body = TextAreaField("Справка", validators=[DataRequired(), Length(min=50)])
    submit = SubmitField("Сохранить справку")
