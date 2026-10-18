import pytest
from rest_framework.test import APIClient

from apps.system.models import DataScope, Menu, MenuType, Role, RoleMenu, User, UserRole
from apps.system.services.dept import dept_create


def grant(user, code, scope):
    """授予用户权限。"""
    role = Role.objects.create(name=code, data_scope=scope)
    menu = Menu.objects.create(name=code, type=MenuType.BUTTON, permission_code=code)
    UserRole.objects.create(user=user, role=role)
    RoleMenu.objects.create(role=role, menu=menu)


@pytest.mark.django_db
def test_scoped_user_sees_only_subtree_and_hidden_user_is_404():
    """测试数据范围内的用户只能看到子树内的用户，范围外的用户返回 404。"""
    root = dept_create(name="总公司")
    east = dept_create(name="华东", parent=root)
    shanghai = dept_create(name="上海", parent=east)
    north = dept_create(name="华北", parent=root)
    alice = User.objects.create_user(username="alice", password="pass-12345", dept=east)
    User.objects.create_user(username="bob", password="pass-12345", dept=shanghai)
    carol = User.objects.create_user(username="carol", password="pass-12345", dept=north)
    grant(alice, "system:user:list", DataScope.DEPT_AND_CHILD)
    client = APIClient()
    client.force_authenticate(user=alice)

    listed = client.get("/api/v1/system/users")
    hidden = client.get(f"/api/v1/system/users/{carol.id}")

    assert {item["username"] for item in listed.json()["results"]} == {"alice", "bob"}
    assert hidden.status_code == 404


@pytest.mark.django_db
def test_cannot_create_user_in_dept_outside_scope():
    """测试不能在数据范围外的部门创建用户。"""
    root = dept_create(name="总公司")
    east = dept_create(name="华东", parent=root)
    north = dept_create(name="华北", parent=root)
    alice = User.objects.create_user(username="alice", password="pass-12345", dept=east)
    grant(alice, "system:user:create", DataScope.DEPT_AND_CHILD)
    client = APIClient()
    client.force_authenticate(user=alice)

    rejected = client.post(
        "/api/v1/system/users",
        {"username": "dave", "password": "pass-12345", "dept_id": north.id},
        format="json",
    )
    created = client.post(
        "/api/v1/system/users",
        {"username": "dave", "password": "pass-12345", "dept_id": east.id},
        format="json",
    )

    assert rejected.status_code == 404
    assert created.status_code == 201
    assert created.json()["dept_id"] == east.id


@pytest.mark.django_db
def test_user_cannot_delete_self():
    """测试用户不能删除自己。"""
    admin = User.objects.create_superuser(username="root", password="pass-12345")
    client = APIClient()
    client.force_authenticate(user=admin)

    deleted = client.delete(f"/api/v1/system/users/{admin.id}")

    assert deleted.status_code == 400
    assert deleted.json()["code"] == "cannot_delete_self"
