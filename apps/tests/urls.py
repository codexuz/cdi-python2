# apps/tests/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestViewSet, QuestionSetViewSet

router = DefaultRouter()
router.register(r"", TestViewSet, basename="tests")
router.register(r"question-sets", QuestionSetViewSet, basename="question-sets")

urlpatterns = [path("", include(router.urls))]
