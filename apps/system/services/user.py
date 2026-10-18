from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.system.models import Dept, User, UserStatus


class UserError(Exception):
    """用户操作错误。"""
    def __init__(self, code, message):
        self.code = code
        self.message = message


def user_create(*, username: str, password: str, phone: str, status: str, dept: Dept) -> User:
    """创建用户。"""
    try:
        validate_password(password)
    except ValidationError as exc:
        raise UserError("invalid_password", "；".join(exc.messages))
    try:
        return User.objects.create_user(
            username=username,
            password=password,
            phone=phone,
            status=status,
            dept=dept,
        )
    except IntegrityError:
        raise UserError("username_taken", "用户名已存在")


def user_update(*, user: User, phone: str, status: str, dept: Dept, password: str | None) -> User:
    """更新用户。"""
    if password is not None:
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            raise UserError("invalid_password", "；".join(exc.messages))
        user.set_password(password)
    user.phone = phone
    user.status = status
    user.dept = dept
    user.save()
    return user


def user_delete(*, actor: User, user: User) -> None:
    """删除用户。"""
    if actor.id == user.id:
        raise UserError("cannot_delete_self", "不能删除自己")
    if user.is_superuser and not actor.is_superuser:
        raise UserError("cannot_delete_superuser", "不能删除超级用户")
    user.delete()
