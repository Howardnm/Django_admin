from django.urls import path

from apps.system.api.auth import LoginView, LogoutView, MeView, RefreshView
from apps.system.api.depts import DeptCollectionView, DeptDetailView

urlpatterns = [
    path("auth/login", LoginView.as_view()),
    path("auth/refresh", RefreshView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("auth/me", MeView.as_view()),
    path("system/depts", DeptCollectionView.as_view()),
    path("system/depts/<int:dept_id>", DeptDetailView.as_view()),
]
