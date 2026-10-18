import pytest
from rest_framework.test import APIClient

from apps.system.models import DataScope, User, UserRole
from apps.system.services.dept import dept_create


@pytest.mark.django_db
def test_create_list_and_reject_duplicate_name():
    """测试创建角色、列出角色以及拒绝重复名称的角色。"""
    admin = User.objects.create_superuser(username="root", password="pass-12345")
    client = APIClient()
    client.force_authenticate(user=admin)

    created = client.post(
        "/api/v1/system/roles",
        {"name": "审计", "data_scope": DataScope.SELF},
        format="json",
    )
    listed = client.get("/api/v1/system/roles")
    duplicated = client.post(
        "/api/v1/system/roles",
        {"name": "审计", "data_scope": DataScope.ALL},
        format="json",
    )

    assert created.status_code == 201
    assert created.json()["data_scope"] == "self"
    assert listed.json()["count"] == 1
    assert duplicated.status_code == 400
    assert duplicated.json()["code"] == "name_taken"


@pytest.mark.django_db
def test_delete_role_assigned_to_user_is_rejected():
    """测试删除已分配给用户的角色被拒绝。"""
    admin = User.objects.create_superuser(username="root", password="pass-12345")
    dept = dept_create(name="总公司")
    member = User.objects.create_user(username="alice", password="pass-12345", dept=dept)
    client = APIClient()
    client.force_authenticate(user=admin)
    created = client.post(
        "/api/v1/system/roles",
        {"name": "审计", "data_scope": DataScope.SELF},
        format="json",
    )
    UserRole.objects.create(user=member, role_id=created.json()["id"])

    deleted = client.delete(f"/api/v1/system/roles/{created.json()['id']}")

    assert deleted.status_code == 400
    assert deleted.json()["code"] == "role_in_use"


@pytest.mark.django_db
def test_user_without_role_permission_is_forbidden():
    """测试没有角色权限的用户被禁止访问角色API。"""
    dept = dept_create(name="总公司")
    user = User.objects.create_user(username="alice", password="pass-12345", dept=dept)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/v1/system/roles")

    assert response.status_code == 403
