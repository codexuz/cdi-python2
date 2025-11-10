#  apps/users/urls.py
from django.urls import path
from .views import MeView, UsersListView, UserDetailView, toggle_status

urlpatterns = [
    path("me/", MeView.as_view(), name="users-me"),
    path("", UsersListView.as_view(), name="users-list"),
    path("<uuid:pk>/", UserDetailView.as_view(), name="users-detail"),
    path("<uuid:pk>/status/", toggle_status, name="users-toggle-status"),
]
