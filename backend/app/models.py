from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager


class TimestampMixin:
    """Общий миксин с временными метками"""

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


class Role(db.Model):
    """Роли пользователей (администратор, менеджер, клиент и т.д.)"""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.String(255))
    level = db.Column(db.Integer, default=10)

    users = db.relationship("UserRole", back_populates="role", cascade="all, delete")

    @staticmethod
    def get_or_create(name: str, description: str = "", level: int = 10) -> "Role":
        """Гарантирует наличие роли в базе данных"""

        role = Role.query.filter_by(name=name).first()
        if role:
            return role

        role = Role(name=name, description=description, level=level)
        db.session.add(role)
        db.session.commit()
        return role

    def __repr__(self) -> str:  # pragma: no cover - служебный вывод
        return f"Role(name={self.name!r})"


class User(UserMixin, TimestampMixin, db.Model):
    """Пользователи системы барахолки"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(32))
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)

    items = db.relationship("Item", back_populates="owner", lazy="dynamic")
    donations = db.relationship(
        "Donation",
        back_populates="donor",
        lazy="dynamic",
        foreign_keys="Donation.donor_id",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    roles = db.relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    comments = db.relationship(
        "Comment",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name: str) -> bool:
        return any(link.role.name == role_name for link in self.roles)

    def to_dict(self) -> dict:
        """Упрощённое представление пользователя для API"""

        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "roles": [link.role.name for link in self.roles],
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"User(username={self.username!r})"


class UserRole(db.Model):
    """Связующая таблица пользователь ↔ роль"""

    __tablename__ = "user_roles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)

    user = db.relationship("User", back_populates="roles")
    role = db.relationship("Role", back_populates="users")


class HazardClass(db.Model):
    """Класс опасности предмета для правильной утилизации"""

    __tablename__ = "hazard_classes"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)

    items = db.relationship("Item", back_populates="hazard_class", lazy="dynamic")


class RecyclingMethod(db.Model):
    """Способы переработки"""

    __tablename__ = "recycling_methods"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    instructions = db.Column(db.Text)
    requires_special_license = db.Column(db.Boolean, default=False)

    items = db.relationship("Item", back_populates="recycling_method", lazy="dynamic")


class Category(db.Model):
    """Категории предметов (с возможностью иерархии)"""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey("categories.id"))

    parent = db.relationship("Category", remote_side=[id], backref="children")
    items = db.relationship("Item", back_populates="category", lazy="dynamic")

    @staticmethod
    def seed_defaults():
        defaults = [
            ("Электроника", "Телефоны, ноутбуки, гаджеты"),
            ("Бытовая техника", "Чайники, стиральные машины, миксеры"),
            ("Одежда", "Вещи, обувь, аксессуары"),
            ("Детские товары", "Игрушки, мебель, коляски"),
        ]
        for name, desc in defaults:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name, description=desc))
        db.session.commit()


class Item(TimestampMixin, db.Model):
    """Объявление о вещи"""

    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float)
    is_free = db.Column(db.Boolean, default=False)
    is_exchangeable = db.Column(db.Boolean, default=False)
    status = db.Column(
        db.String(20),
        default="available",
    )  # available, reserved, donated, recycled, disposed

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    hazard_class_id = db.Column(db.Integer, db.ForeignKey("hazard_classes.id"))
    recycling_method_id = db.Column(db.Integer, db.ForeignKey("recycling_methods.id"))

    owner = db.relationship("User", back_populates="items")
    category = db.relationship("Category", back_populates="items")
    hazard_class = db.relationship("HazardClass", back_populates="items")
    recycling_method = db.relationship("RecyclingMethod", back_populates="items")
    documents = db.relationship(
        "ItemDocument",
        back_populates="item",
        cascade="all, delete-orphan",
    )
    images = db.relationship(
        "ItemImage",
        backref="item",
        cascade="all, delete-orphan",
        lazy=True
    )
    comments = db.relationship(
        "Comment",
        back_populates="item",
        cascade="all, delete-orphan",
        lazy=True
    )
    disposal_requests = db.relationship(
        "DisposalRequest",
        back_populates="item",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"Item(title={self.title!r}, status={self.status})"

    def to_dict(self) -> dict:
        """Сериализация сущности для передачи в клиент"""

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "condition": self.condition,
            "price": self.price,
            "is_free": self.is_free,
            "is_exchangeable": self.is_exchangeable,
            "status": self.status,
            "category": self.category.name if self.category else None,
            "hazard_class": self.hazard_class.code if self.hazard_class else None,
            "recycling_method": self.recycling_method.name if self.recycling_method else None,
            "owner": self.owner.username if self.owner else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ItemDocument(TimestampMixin, db.Model):
    """Прикреплённые файлы и паспорта изделия"""

    __tablename__ = "item_documents"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    item = db.relationship("Item", back_populates="documents")


class ItemImage(TimestampMixin, db.Model):
    """Изображения для объявлений"""

    __tablename__ = "item_images"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)  # Основное изображение
    item = db.relationship("Item", back_populates="images")


class Comment(TimestampMixin, db.Model):
    """Комментарии под объявлениями"""

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)

    item = db.relationship("Item", back_populates="comments")
    user = db.relationship("User", back_populates="comments")


class FeedbackMessage(TimestampMixin, db.Model):
    """Сообщения обратной связи от посетителей"""

    __tablename__ = "feedback_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)



class ExchangeRequest(TimestampMixin, db.Model):
    """Заявки на обмен вещами"""

    __tablename__ = "exchange_requests"

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    offered_item_id = db.Column(db.Integer, db.ForeignKey("items.id"))
    status = db.Column(
        db.String(20),
        default="pending",
    )  # pending, accepted, declined, cancelled
    message = db.Column(db.Text)

    requester = db.relationship("User", foreign_keys=[requester_id])
    target_item = db.relationship("Item", foreign_keys=[target_item_id], backref="incoming_requests")
    offered_item = db.relationship("Item", foreign_keys=[offered_item_id], backref="offered_in_requests")


class Donation(TimestampMixin, db.Model):
    """Учёт пожертвований"""

    __tablename__ = "donations"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.String(20), default="pending")
    confirmation_doc = db.Column(db.String(255))

    item = db.relationship("Item", backref="donations")
    donor = db.relationship("User", foreign_keys=[donor_id], back_populates="donations")
    recipient = db.relationship("User", foreign_keys=[recipient_id])


class RecyclingOperation(TimestampMixin, db.Model):
    """Факт переработки предметов"""

    __tablename__ = "recycling_operations"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    method = db.Column(db.String(120))
    location = db.Column(db.String(255))
    notes = db.Column(db.Text)

    item = db.relationship("Item", backref="recycling_operations")
    operator = db.relationship("User", foreign_keys=[operator_id])


class DisposalRequest(TimestampMixin, db.Model):
    """Заявка на утилизацию (если переработка невозможна)"""

    __tablename__ = "disposal_requests"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    requested_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")
    hazard_notes = db.Column(db.Text)

    item = db.relationship("Item", back_populates="disposal_requests")
    requested_by = db.relationship("User", foreign_keys=[requested_by_id])


class ActivityLog(TimestampMixin, db.Model):
    """Журнал действий в системе"""

    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    event_type = db.Column(db.String(64), nullable=False)
    payload = db.Column(db.JSON)

    user = db.relationship("User")


class Notification(TimestampMixin, db.Model):
    """Уведомления пользователям"""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="notifications")


class SystemSetting(db.Model):
    """Настройки системы, используемые админом"""

    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255))

