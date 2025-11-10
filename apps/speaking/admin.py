#  apps/speaking/admin.py
from django.contrib import admin
from .models import SpeakingRequest


@admin.register(SpeakingRequest)
class SpeakingRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "fee_amount", "currency", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = (
        "student__user__fullname",
        "student__user__phone_number",
        "student__user__telegram_username",
        "id",
    )
    raw_id_fields = ("student",)
    ordering = ("-created_at",)
