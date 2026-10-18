from django.db.models import Q, QuerySet

from apps.system.models import DataScope, Dept, Menu, MenuType, Role, User, UserRole


def permission_codes_for(*, user: User) -> set[str]:
    """ 获取用户的权限码集合，超级用户返回所有权限码，普通用户返回其角色所拥有的权限码 """
    if user.is_superuser:
        # 查询菜单模型，排除空字符串，只返回permission_code字段的值，并将其转换为集合
        codes = Menu.objects.exclude(permission_code="").values_list("permission_code", flat=True)
        return set(codes)

    # 查询菜单模型，通过关联表role_menus和user_roles，筛选出用户所拥有的角色，并且角色是启用的，然后排除空字符串，只返回permission_code字段的值，并将其转换为集合 
    # 原理：
    # role_menus：菜单 → 角色菜单关联表
    # role_menus__role：再跳到关联的角色
    # role_menus__role__user_roles：从这个角色再跳到用户角色关联表
    # role_menus__role__user_roles__user：最终跳到用户
    codes = (
        Menu.objects.filter(
            role_menus__role__user_roles__user=user,
            role_menus__role__is_enabled=True,
        )
        .exclude(permission_code="")
        .values_list("permission_code", flat=True)
    )
    return set(codes)


def _scope_rank(scope: str) -> int:
    """ 数据范围的等级，范围越大等级越高，用于比较两个数据范围的大小 """
    return {
        DataScope.ALL: 4,
        DataScope.CUSTOM: 3,
        DataScope.DEPT_AND_CHILD: 2,
        DataScope.DEPT: 1,
        DataScope.SELF: 0,
    }[scope]


def scope_depts_for(*, user: User) -> QuerySet[Dept] | None:
    """
    获取用户可访问的部门列表，超级用户返回 None，表示不限制部门，普通用户返回其角色所拥有的数据范围内的部门列表。
    None 表示不限制部门。空 QuerySet 表示看不到任何部门。
    """
    if user.is_superuser:
        return None
    roles = list(Role.objects.filter(user_roles__user=user, is_enabled=True).distinct())
    if not roles:
        return Dept.objects.none()
    if any(role.data_scope == DataScope.ALL for role in roles):
        return None

    query = Q()
    for role in roles:
        if role.data_scope == DataScope.DEPT and user.dept_id is not None:
            query |= Q(id=user.dept_id)
        elif role.data_scope == DataScope.DEPT_AND_CHILD and user.dept_id is not None:
            query |= Q(path__startswith=user.dept.path)
        elif role.data_scope == DataScope.CUSTOM:
            query |= Q(role_depts__role=role)
    if not query:
        return Dept.objects.none()
    return Dept.objects.filter(query).distinct()



def users_visible_to(*, user: User) -> QuerySet[User]:
    """
    获取用户可访问的用户列表，超级用户返回所有用户，普通用户返回其角色所拥有的数据范围内的用户列表。
    如果用户没有任何角色，或者用户的部门为空且其角色中有数据范围不为自定义的角色，则返回空的QuerySet。
    如果用户的角色中有数据范围为 “全部” 的角色，则返回所有用户。
    """
    if user.is_superuser:
        return User.objects.all()
    roles = Role.objects.filter(user_roles__user=user, is_enabled=True)
    scopes = set(roles.values_list("data_scope", flat=True))
    if not scopes:
        return User.objects.none()
    if DataScope.ALL in scopes:
        return User.objects.all()

    query = Q()
    if DataScope.DEPT in scopes and user.dept_id is not None:
        query |= Q(dept_id=user.dept_id)
    if DataScope.DEPT_AND_CHILD in scopes and user.dept_id is not None:
        query |= Q(dept__path__startswith=user.dept.path)
    if DataScope.SELF in scopes:
        query |= Q(id=user.id)
    if DataScope.CUSTOM in scopes:
        dept_ids = Dept.objects.filter(role_depts__role__in=roles).values("id")
        query |= Q(dept_id__in=dept_ids)
    if not query:
        return User.objects.none()
    return User.objects.filter(query).distinct()
