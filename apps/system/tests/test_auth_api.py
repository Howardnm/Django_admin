import pytest
from rest_framework.test import APIClient

from apps.system.models import DataScope, Menu, MenuType, Role, RoleMenu, User, UserRole, UserStatus
from apps.system.services.dept import dept_create


@pytest.mark.django_db
def test_login_me_and_disabled_user():
    """ 测试登录、获取个人信息以及停用用户的情况 """
    dept = dept_create(name="总公司")
    User.objects.create_user(username="alice", password="pass-12345", dept=dept)
    client = APIClient()

    response = client.post("/api/v1/auth/login", {"username": "alice", "password": "pass-12345"}, format="json")
    assert response.status_code == 200
    access = response.json()["access"]

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "alice"

    User.objects.filter(username="alice").update(status=UserStatus.DISABLED)
    rejected = APIClient().post("/api/v1/auth/login", {"username": "alice", "password": "pass-12345"}, format="json")
    assert rejected.status_code == 400
    assert rejected.json()["code"] == "user_disabled"


@pytest.mark.django_db
def test_me_includes_ancestor_menus_but_not_buttons():
    """ 测试获取个人信息时，菜单包含祖先菜单，但不包含按钮类型的菜单 """
    dept = dept_create(name="总公司")
    user = User.objects.create_user(username="alice", password="pass-12345", dept=dept)
    catalog = Menu.objects.create(name="系统管理", type=MenuType.CATALOG, route="/system")
    page = Menu.objects.create(name="用户管理", type=MenuType.MENU, parent=catalog, route="/system/users")
    button = Menu.objects.create(
        name="新增用户",
        type=MenuType.BUTTON,
        parent=page,
        permission_code="system:user:create",
    )
    hidden = Menu.objects.create(name="日志", type=MenuType.CATALOG, route="/audit")
    role = Role.objects.create(name="用户页", data_scope=DataScope.SELF)
    RoleMenu.objects.create(role=role, menu=page)
    RoleMenu.objects.create(role=role, menu=button)
    UserRole.objects.create(user=user, role=role)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/auth/me")
    menus = response.json()["menus"]
    names = {item["name"] for item in menus}
    page_row = next(item for item in menus if item["name"] == "用户管理")

    assert response.status_code == 200
    assert names == {"系统管理", "用户管理"}
    assert page_row["parent_id"] == catalog.id
    assert hidden.name not in names
    assert "system:user:create" in response.json()["permission_codes"]
