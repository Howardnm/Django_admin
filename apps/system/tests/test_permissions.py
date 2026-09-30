import pytest
from rest_framework.test import APIRequestFactory

from apps.system.models import DataScope, Menu, MenuType, Role, RoleMenu, User, UserRole
from apps.system.permissions import HasPermissionCode
from apps.system.services.dept import dept_create


factory = APIRequestFactory()


class View:
    permission_code = "system:user:list"


@pytest.mark.django_db
def test_permission_code_is_loaded_once_and_checked():
    """ 
    测试权限码只加载一次，并且可以正确检查
    测试场景：
    1. 创建一个用户，分配一个角色，角色分配一个菜单，
    菜单有一个权限码
    2. 创建一个请求，设置请求的用户为上面创建的用户
    3. 调用 HasPermissionCode().has_permission(request, view) 方法，检查是否有权限
    4. 检查 request.user.permission_codes 是否包含菜单的权限码
    """
    dept = dept_create(name="总公司")
    user = User.objects.create_user(username="alice", password="pass-12345", dept=dept)
    role = Role.objects.create(name="查询", data_scope=DataScope.SELF)
    menu = Menu.objects.create(
        name="用户列表", type=MenuType.BUTTON, permission_code="system:user:list"
    )
    UserRole.objects.create(user=user, role=role)
    RoleMenu.objects.create(role=role, menu=menu)
    request = factory.get("/users")
    request.user = user

    assert HasPermissionCode().has_permission(request, View()) is True
    assert request.user.permission_codes == {"system:user:list"}


@pytest.mark.django_db
def test_missing_permission_code_is_denied():
    """ 测试缺少权限码时，访问被拒绝 """
    dept = dept_create(name="总公司")
    user = User.objects.create_user(username="alice", password="pass-12345", dept=dept)
    request = factory.get("/users")
    request.user = user

    assert HasPermissionCode().has_permission(request, View()) is False
