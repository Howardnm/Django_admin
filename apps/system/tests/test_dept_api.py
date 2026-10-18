import pytest
from rest_framework.test import APIClient

from apps.system.models import DataScope, Menu, MenuType, Role, RoleMenu, User, UserRole
from apps.system.services.dept import dept_create


def grant(user, code, scope):
    """给用户授予权限码和数据范围。"""
    role = Role.objects.create(name=code, data_scope=scope)
    menu = Menu.objects.create(name=code, type=MenuType.BUTTON, permission_code=code)
    UserRole.objects.create(user=user, role=role)
    RoleMenu.objects.create(role=role, menu=menu)


@pytest.mark.django_db
def test_superuser_lists_flat_tree_and_move_keeps_descendants():
    """超级管理员可以看到所有部门，并且移动部门时会保持子孙部门的路径不变。"""
    client = APIClient()
    admin = User.objects.create_superuser(username="root", password="pass-12345")
    client.force_authenticate(user=admin)
    root = client.post("/api/v1/system/depts", {"name": "总公司", "parent_id": None}, format="json")
    child = client.post(
        "/api/v1/system/depts",
        {"name": "华东", "parent_id": root.json()["id"]},
        format="json",
    )
    grandchild = client.post(
        "/api/v1/system/depts",
        {"name": "上海", "parent_id": child.json()["id"]},
        format="json",
    )
    moved = client.put(
        f"/api/v1/system/depts/{child.json()['id']}",
        {"name": "华东", "parent_id": None, "sort": 1},
        format="json",
    )

    listed = client.get("/api/v1/system/depts")
    names = {item["name"] for item in listed.json()}
    grandchild_row = next(item for item in listed.json() if item["id"] == grandchild.json()["id"])

    assert root.status_code == 201
    assert moved.status_code == 200
    assert names == {"总公司", "华东", "上海"}
    assert grandchild_row["parent_id"] == child.json()["id"]
    assert moved.json()["parent_id"] is None


@pytest.mark.django_db
def test_scoped_user_cannot_see_or_attach_to_other_branch():
    """有数据范围的用户不能看到或挂靠到其他分支的部门。"""
    root = dept_create(name="总公司")
    east = dept_create(name="华东", parent=root)
    north = dept_create(name="华北", parent=root)
    user = User.objects.create_user(username="alice", password="pass-12345", dept=east)
    grant(user, "system:dept:list", DataScope.DEPT_AND_CHILD)
    grant(user, "system:dept:create", DataScope.DEPT_AND_CHILD)
    grant(user, "system:dept:update", DataScope.DEPT_AND_CHILD)
    client = APIClient()
    client.force_authenticate(user=user)

    listed = client.get("/api/v1/system/depts")
    hidden = client.put(
        f"/api/v1/system/depts/{north.id}",
        {"name": "华北", "parent_id": east.id},
        format="json",
    )
    attached = client.post(
        "/api/v1/system/depts",
        {"name": "暗中挂靠", "parent_id": north.id},
        format="json",
    )

    assert {item["name"] for item in listed.json()} == {"华东"}
    assert hidden.status_code == 404
    assert attached.status_code == 404


@pytest.mark.django_db
def test_delete_dept_with_child_is_rejected():
    """删除有子部门的部门会被拒绝。"""
    client = APIClient()
    admin = User.objects.create_superuser(username="root", password="pass-12345")
    client.force_authenticate(user=admin)
    root = client.post("/api/v1/system/depts", {"name": "总公司", "parent_id": None}, format="json")
    client.post(
        "/api/v1/system/depts",
        {"name": "华东", "parent_id": root.json()["id"]},
        format="json",
    )

    deleted = client.delete(f"/api/v1/system/depts/{root.json()['id']}")

    assert deleted.status_code == 400
    assert deleted.json()["code"] == "dept_in_use"
