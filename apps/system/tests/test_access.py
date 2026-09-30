import pytest

from apps.system.models import DataScope, Dept, Menu, MenuType, Role, RoleDept, RoleMenu, User, UserRole
from apps.system.selectors.access import permission_codes_for, users_visible_to
from apps.system.services.dept import dept_create


def make_user(name, dept):
    return User.objects.create_user(username=name, password="pass-12345", dept=dept)


def grant(user, role, menu):
    UserRole.objects.create(user=user, role=role)
    RoleMenu.objects.create(role=role, menu=menu)


@pytest.mark.django_db
def test_permission_codes_come_from_enabled_roles():
    """ 测试用户的权限码来自其启用的角色，而不是停用的角色 """
    root = dept_create(name="总公司")
    user = make_user("alice", root)
    menu = Menu.objects.create(name="新增用户", type=MenuType.BUTTON, permission_code="system:user:create")
    enabled = Role.objects.create(name="启用角色", data_scope=DataScope.SELF)
    disabled = Role.objects.create(name="停用角色", data_scope=DataScope.ALL, is_enabled=False)
    grant(user, enabled, menu)
    hidden = Menu.objects.create(name="删除用户", type=MenuType.BUTTON, permission_code="system:user:delete")
    RoleMenu.objects.create(role=disabled, menu=hidden)
    UserRole.objects.create(user=user, role=disabled)

    assert permission_codes_for(user=user) == {"system:user:create"}


@pytest.mark.django_db
def test_dept_and_child_scope_includes_descendants_only():
    """ 测试数据范围为本部门及以下的角色只能看到其部门及其子部门的用户 """
    root = dept_create(name="总公司")
    east = dept_create(name="华东", parent=root)
    shanghai = dept_create(name="上海", parent=east)
    other = dept_create(name="华北", parent=root)
    user = make_user("alice", east)
    role = Role.objects.create(name="华东负责人", data_scope=DataScope.DEPT_AND_CHILD)
    UserRole.objects.create(user=user, role=role)
    make_user("bob", shanghai)
    make_user("carol", other)

    visible = set(users_visible_to(user=user).values_list("username", flat=True))

    assert visible == {"alice", "bob"}


@pytest.mark.django_db
def test_custom_scope_uses_checked_depts():
    """ 测试数据范围为自定义部门的角色只能看到其所选部门的用户 """
    root = dept_create(name="总公司")
    east = dept_create(name="华东", parent=root)
    north = dept_create(name="华北", parent=root)
    user = make_user("alice", east)
    role = Role.objects.create(name="指定部门", data_scope=DataScope.CUSTOM)
    RoleDept.objects.create(role=role, dept=north)
    UserRole.objects.create(user=user, role=role)
    make_user("bob", north)

    visible = set(users_visible_to(user=user).values_list("username", flat=True))

    assert visible == {"bob"}


@pytest.mark.django_db
def test_multiple_roles_merge_scopes():
    """ 测试用户拥有多个角色时，数据范围会合并 """
    root = dept_create(name="总公司")
    east = dept_create(name="华东", parent=root)
    user = make_user("alice", east)
    self_role = Role.objects.create(name="本人", data_scope=DataScope.SELF)
    all_role = Role.objects.create(name="全部", data_scope=DataScope.ALL)
    UserRole.objects.create(user=user, role=self_role)
    UserRole.objects.create(user=user, role=all_role)
    make_user("bob", root)

    visible = set(users_visible_to(user=user).values_list("username", flat=True))

    assert visible == {"alice", "bob"}
