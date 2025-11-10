# config/urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/profiles/", include("apps.profiles.urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/user-tests/", include("apps.user_tests.urls")),
    path("api/teacher-checking/", include("apps.teacher_checking.urls")),
    path("api/tests/", include("apps.tests.urls")),
    path("api/payments/", include("apps.payments.urls")),
    path("api/speaking/", include("apps.speaking.urls")),
    # API schema & docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
