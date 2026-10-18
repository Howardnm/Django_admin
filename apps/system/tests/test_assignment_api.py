import pytest
from rest_framework.test import APIClient

from apps.system.models import DataScope, Menu, MenuType, Role, RoleMenu, User, UserRole
from apps.system.services.dept import dept_create


def grant(user, code, scope):
    """为用户授予权限。"""
    role = Role.objects.create(name=code, data_scope=scope)
    menu = Menu.objects.create(name=code, type=MenuType.BUTTON, permission_code=code)
    UserRole.objects.create(user=user, role=role)
    RoleMenu.objects.create(role=role, menu=menu)
    return role


@pytest.mark.django_db
def test_cannot_assign_role_to_user_outside_scope():
    """测试用户无法为不在可见范围内的用户分配角色。"""
    root = dept_create(name="总公司")
    east = dept_create(name="华东", parent=root)
    north = dept_create(name="华北", parent=root)
    alice = User.objects.create_user(username="alice", password="pass-12345", dept=east)
    carol = User.objects.create_user(username="carol", password="pass-12345", dept=north)
    grant(alice, "system:user:assign-role", DataScope.DEPT)
    target_role = Role.objects.create(name="本人", data_scope=DataScope.SELF)
    client = APIClient()
    client.force_authenticate(user=alice)

    response = client.put(
        f"/api/v1/system/users/{carol.id}/roles",
        {"ids": [target_role.id]},
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_cannot_grant_a_wider_role():
    """测试用户无法为其他用户分配比自己更宽的数据范围的角色。"""
    dept = dept_create(name="总公司")
    alice = User.objects.create_user(username="alice", password="pass-12345", dept=dept)
    bob = User.objects.create_user(username="bob", password="pass-12345", dept=dept)
    grant(alice, "system:user:assign-role", DataScope.DEPT)
    wide = Role.objects.create(name="全部", data_scope=DataScope.ALL)
    client = APIClient()
    client.force_authenticate(user=alice)

    response = client.put(
        f"/api/v1/system/users/{bob.id}/roles",
        {"ids": [wide.id]},
        format="json",
    )

    assert response.status_code == 403
    assert response.json()["code"] == "privilege_escalation"


@pytest.mark.django_db
def test_only_custom_role_accepts_depts():
    """测试只有自定义数据范围的角色可以分配部门。"""
    admin = User.objects.create_superuser(username="root", password="pass-12345")
    dept = dept_create(name="总公司")
    client = APIClient()
    client.force_authenticate(user=admin)
    self_role = Role.objects.create(name="本人", data_scope=DataScope.SELF)
    custom_role = Role.objects.create(name="指定", data_scope=DataScope.CUSTOM)

    rejected = client.put(
        f"/api/v1/system/roles/{self_role.id}/depts",
        {"ids": [dept.id]},
        format="json",
    )
    accepted = client.put(
        f"/api/v1/system/roles/{custom_role.id}/depts",
        {"ids": [dept.id]},
        format="json",
    )

    assert rejected.status_code == 400
    assert rejected.json()["code"] == "invalid_scope"
    assert accepted.status_code == 200
    assert accepted.json()["ids"] == [dept.id]
