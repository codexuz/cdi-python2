#  apps/tests/apps.py
from django.apps import AppConfig


class ExamConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tests"
    verbose_name = "IELTS Tests"

    def ready(self):
        from . import signals  # noqa
        from . import signals_m2m  # noqa
