"""Утилита управления ролями пользователей.
Примеры (Windows PowerShell):
  # Показать роли одного пользователя
  #   python .\scripts\manage_roles.py list --user admin
  # Показать всех пользователей с ролями
  #   python .\scripts\manage_roles.py list
  # Выдать роль
  #   python .\scripts\manage_roles.py add  --user ivan --role manager
  # Забрать роль
  #   python .\scripts\manage_roles.py remove --user ivan --role manager
"""
import sys
import argparse
from typing import Optional, List
from backend.app import create_app, db  # type: ignore
from backend.app.models import User, Role, UserRole  # type: ignore


def list_roles(username: Optional[str] = None):
    if username:
        u = User.query.filter_by(username=username).first()
        if not u:
            print(f"[!] Пользователь {username!r} не найден")
            return
        roles = [link.role.name for link in u.roles]
        print(f"{u.username}: {', '.join(roles) if roles else '(нет ролей)'}")
        return
    # все пользователи
    for u in User.query.order_by(User.username).all():
        roles = [link.role.name for link in u.roles]
        print(f"{u.username}: {', '.join(roles) if roles else '(нет ролей)'}")


def add_role(username: str, role_name: str):
    u = User.query.filter_by(username=username).first()
    if not u:
        print(f"[!] Пользователь {username!r} не найден")
        return
    role = Role.get_or_create(role_name)
    if any(link.role_id == role.id for link in u.roles):
        print(f"[=] У {username} уже есть роль {role_name}")
        return
    db.session.add(UserRole(user_id=u.id, role_id=role.id))
    db.session.commit()
    print(f"[OK] Роль {role_name} выдана пользователю {username}")


def remove_role(username: str, role_name: str):
    u = User.query.filter_by(username=username).first()
    if not u:
        print(f"[!] Пользователь {username!r} не найден")
        return
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        print(f"[!] Роль {role_name!r} не найдена")
        return
    link = next((l for l in u.roles if l.role_id == role.id), None)
    if not link:
        print(f"[=] У {username} нет роли {role_name}")
        return
    db.session.delete(link)
    db.session.commit()
    print(f"[OK] Роль {role_name} снята у пользователя {username}")


def main(argv: List[str]):
    parser = argparse.ArgumentParser(description="Управление ролями")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="Показать роли")
    p_list.add_argument("--user", dest="user", help="Логин пользователя", default=None)

    p_add = sub.add_parser("add", help="Выдать роль пользователю")
    p_add.add_argument("--user", required=True)
    p_add.add_argument("--role", required=True, choices=["admin", "manager", "client"])  # допустимые роли

    p_rm = sub.add_parser("remove", help="Снять роль у пользователя")
    p_rm.add_argument("--user", required=True)
    p_rm.add_argument("--role", required=True)

    args = parser.parse_args(argv)

    app = create_app()
    with app.app_context():
        if args.cmd == "list":
            list_roles(args.user)
        elif args.cmd == "add":
            add_role(args.user, args.role)
        elif args.cmd == "remove":
            remove_role(args.user, args.role)


if __name__ == "__main__":
    main(sys.argv[1:])
