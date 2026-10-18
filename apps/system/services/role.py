from django.db import IntegrityError

from apps.system.models import Role


class RoleError(Exception):
    """角色操作异常"""
    def __init__(self, code, message):
        self.code = code
        self.message = message


def role_create(*, name: str, data_scope: str, sort: int, is_enabled: bool) -> Role:
    """创建角色"""
    try:
        return Role.objects.create(
            name=name,
            data_scope=data_scope,
            sort=sort,
            is_enabled=is_enabled,
        )
    except IntegrityError:
        raise RoleError("name_taken", "角色名称已存在")


def role_update(*, role: Role, name: str, data_scope: str, sort: int, is_enabled: bool) -> Role:
    """更新角色"""
    role.name = name
    role.data_scope = data_scope
    role.sort = sort
    role.is_enabled = is_enabled
    try:
        role.save()
    except IntegrityError:
        raise RoleError("name_taken", "角色名称已存在")
    return role


def role_delete(*, role: Role) -> None:
    """删除角色"""
    if role.user_roles.exists():
        raise RoleError("role_in_use", "角色已分配给用户")
    role.delete()
