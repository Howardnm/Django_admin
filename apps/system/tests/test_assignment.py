import pytest

from apps.system.models import DataScope, Menu, MenuType, Role, User
from apps.system.services.assignment import PrivilegeEscalationError, assign_role_menus, assign_user_roles
from apps.system.services.dept import dept_create


def make_user(name, dept):
    return User.objects.create_user(username=name, password="pass-12345", dept=dept)


@pytest.mark.django_db
def test_actor_cannot_grant_a_wider_role():
    """ 测试一个用户不能授予比自己数据范围更宽的角色 """
    dept = dept_create(name="总公司")
    actor = make_user("alice", dept)
    target = make_user("bob", dept)
    own_role = Role.objects.create(name="本人", data_scope=DataScope.SELF)
    wide_role = Role.objects.create(name="全部", data_scope=DataScope.ALL)
    assign_user_roles(actor=actor, user=actor, roles=[])
    actor.roles.add(own_role)

    with pytest.raises(PrivilegeEscalationError):
        assign_user_roles(actor=actor, user=target, roles=[wide_role])


@pytest.mark.django_db
def test_button_without_permission_code_is_rejected():
    """ 测试按钮必须有权限码 """
    dept = dept_create(name="总公司")
    actor = make_user("alice", dept)
    actor.is_superuser = True
    actor.save(update_fields=["is_superuser"])
    role = Role.objects.create(name="管理员", data_scope=DataScope.ALL)
    button = Menu.objects.create(name="新增用户", type=MenuType.BUTTON, permission_code="")

    with pytest.raises(ValueError):
        assign_role_menus(actor=actor, role=role, menus=[button])
