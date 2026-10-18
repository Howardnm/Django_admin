from django.urls import path

from apps.system.api.auth import LoginView, LogoutView, MeView, RefreshView

urlpatterns = [
    path("auth/login", LoginView.as_view()),
    path("auth/refresh", RefreshView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("auth/me", MeView.as_view()),
]
