import pytest
from rest_framework.test import APIClient

from apps.system.models import User, UserStatus
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
