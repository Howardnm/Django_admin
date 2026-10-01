from django.db import transaction

from apps.system.models import DataScope, Menu, MenuType, Role, RoleDept, RoleMenu, User, UserRole
from apps.system.selectors.access import _scope_rank, permission_codes_for


class PrivilegeEscalationError(Exception):
    pass


def _check_actor_can_grant_role(*, actor: User, role: Role) -> None:
    """ 检查操作人（actor）是否可以授予指定角色 """
    if actor.is_superuser:
        return
    actor_scopes = actor.roles.filter(is_enabled=True).values_list("data_scope", flat=True)
    widest = max((_scope_rank(scope) for scope in actor_scopes), default=-1)
    if _scope_rank(role.data_scope) > widest:
        raise PrivilegeEscalationError("不能授予比自己数据范围更宽的角色")
    role_codes = set(
        Menu.objects.filter(role_menus__role=role)
        .exclude(permission_code="")
        .values_list("permission_code", flat=True)
    )
    if not role_codes.issubset(permission_codes_for(user=actor)):
        raise PrivilegeEscalationError("不能授予自己没有的权限")


def assign_user_roles(*, actor: User, user: User, roles: list[Role]) -> None:
    """ 将指定的角色分配给用户 """
    for role in roles:
        _check_actor_can_grant_role(actor=actor, role=role)
    with transaction.atomic():
        UserRole.objects.filter(user=user).delete()
        UserRole.objects.bulk_create(
            [UserRole(user=user, role=role) for role in roles]
        )


def assign_role_menus(*, actor: User, role: Role, menus: list[Menu]) -> None:
    """ 将指定的菜单分配给角色 """
    if not actor.is_superuser:
        codes = {
            menu.permission_code
            for menu in menus
            if menu.permission_code
        }
        if not codes.issubset(permission_codes_for(user=actor)):
            raise PrivilegeEscalationError("不能分配自己没有的权限")
    buttons = [menu for menu in menus if menu.type == MenuType.BUTTON]
    missing = [menu.name for menu in buttons if not menu.permission_code]
    if missing:
        raise ValueError(f"按钮必须有权限码: {', '.join(missing)}")
    with transaction.atomic():
        RoleMenu.objects.filter(role=role).delete()
        RoleMenu.objects.bulk_create(
            [RoleMenu(role=role, menu=menu) for menu in menus]
        )


def assign_role_depts(*, role: Role, depts: list) -> None:
    """ 将指定的部门分配给角色 """
    if role.data_scope != DataScope.CUSTOM and depts:
        raise ValueError("只有自定义数据范围的角色可以指定部门")
    with transaction.atomic():
        RoleDept.objects.filter(role=role).delete()
        RoleDept.objects.bulk_create(
            [RoleDept(role=role, dept=dept) for dept in depts]
        )
