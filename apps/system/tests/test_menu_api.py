import pytest
from rest_framework.test import APIClient

from apps.system.models import MenuType, User


def payload(name, menu_type, parent_id=None, permission_code=""):
    """生成菜单请求负载。"""
    return {
        "name": name,
        "type": menu_type,
        "parent_id": parent_id,
        "permission_code": permission_code,
        "route": "",
        "sort": 0,
    }


@pytest.mark.django_db
def test_button_requires_unique_permission_code():
    """测试按钮必须有唯一的权限码。"""
    admin = User.objects.create_superuser(username="root", password="pass-12345")
    client = APIClient()
    client.force_authenticate(user=admin)

    missing = client.post(
        "/api/v1/system/menus",
        payload("新增用户", MenuType.BUTTON),
        format="json",
    )
    created = client.post(
        "/api/v1/system/menus",
        payload("新增用户", MenuType.BUTTON, permission_code="system:user:create"),
        format="json",
    )
    duplicated = client.post(
        "/api/v1/system/menus",
        payload("再来一个", MenuType.BUTTON, permission_code="system:user:create"),
        format="json",
    )

    assert missing.status_code == 400
    assert missing.json()["code"] == "button_code_required"
    assert created.status_code == 201
    assert duplicated.status_code == 400
    assert duplicated.json()["code"] == "code_taken"


@pytest.mark.django_db
def test_cannot_move_menu_under_descendant():
    """测试不能将菜单移动到其子孙菜单下。"""
    admin = User.objects.create_superuser(username="root", password="pass-12345")
    client = APIClient()
    client.force_authenticate(user=admin)
    root = client.post("/api/v1/system/menus", payload("系统管理", MenuType.CATALOG), format="json")
    child = client.post(
        "/api/v1/system/menus",
        payload("用户管理", MenuType.MENU, parent_id=root.json()["id"]),
        format="json",
    )

    moved = client.put(
        f"/api/v1/system/menus/{root.json()['id']}",
        payload("系统管理", MenuType.CATALOG, parent_id=child.json()["id"]),
        format="json",
    )

    assert moved.status_code == 400
    assert moved.json()["code"] == "menu_cycle"


@pytest.mark.django_db
def test_delete_menu_with_child_is_rejected():
    """测试删除有子菜单的菜单会被拒绝。"""
    admin = User.objects.create_superuser(username="root", password="pass-12345")
    client = APIClient()
    client.force_authenticate(user=admin)
    root = client.post("/api/v1/system/menus", payload("系统管理", MenuType.CATALOG), format="json")
    client.post(
        "/api/v1/system/menus",
        payload("用户管理", MenuType.MENU, parent_id=root.json()["id"]),
        format="json",
    )

    deleted = client.delete(f"/api/v1/system/menus/{root.json()['id']}")

    assert deleted.status_code == 400
    assert deleted.json()["code"] == "menu_in_use"
