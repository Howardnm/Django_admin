from django.urls import path

from apps.system.api.assignments import RoleDeptAssignView, RoleMenuAssignView, UserRoleAssignView
from apps.system.api.auth import LoginView, LogoutView, MeView, RefreshView
from apps.system.api.depts import DeptCollectionView, DeptDetailView
from apps.system.api.menus import MenuCollectionView, MenuDetailView
from apps.system.api.roles import RoleCollectionView, RoleDetailView
from apps.system.api.users import UserCollectionView, UserDetailView

urlpatterns = [
    path("auth/login", LoginView.as_view()),
    path("auth/refresh", RefreshView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("auth/me", MeView.as_view()),
    path("system/depts", DeptCollectionView.as_view()),
    path("system/depts/<int:dept_id>", DeptDetailView.as_view()),
    path("system/users", UserCollectionView.as_view()),
    path("system/users/<int:user_id>", UserDetailView.as_view()),
    path("system/users/<int:user_id>/roles", UserRoleAssignView.as_view()),
    path("system/roles", RoleCollectionView.as_view()),
    path("system/roles/<int:role_id>", RoleDetailView.as_view()),
    path("system/roles/<int:role_id>/menus", RoleMenuAssignView.as_view()),
    path("system/roles/<int:role_id>/depts", RoleDeptAssignView.as_view()),
    path("system/menus", MenuCollectionView.as_view()),
    path("system/menus/<int:menu_id>", MenuDetailView.as_view()),
]
