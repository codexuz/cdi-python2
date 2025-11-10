# apps/accounts/admin.py
from __future__ import annotations

from datetime import timedelta

from django.contrib import admin, messages
from django.db import transaction
from django.utils.timezone import now, localtime

from .models import VerificationCode


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "purpose",
        "tg_identity",
        "consumed",
        "ttl_seconds_display",
        "created_local",
        "expires_local",
    )
    list_filter = (
        "purpose",
        "consumed",
        ("created_at", admin.DateFieldListFilter),
        ("expires_at", admin.DateFieldListFilter),
    )
    search_fields = (
        "code",
        "telegram_id",
        "telegram_username",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "expires_at")
    fields = (
        "purpose",
        "code",
        "telegram_id",
        "telegram_username",
        "consumed",
        "created_at",
        "expires_at",
    )
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        # Eng kerakli ustunlarni tanlab, admin sahifasini yengil qilamiz
        return (
            super()
            .get_queryset(request)
            .only(
                "id",
                "code",
                "purpose",
                "telegram_id",
                "telegram_username",
                "consumed",
                "created_at",
                "expires_at",
            )
        )

    @admin.display(description="Telegram")
    def tg_identity(self, obj: VerificationCode) -> str:
        if obj.telegram_id and obj.telegram_username:
            return f"{obj.telegram_id} ({obj.telegram_username})"
        if obj.telegram_id:
            return str(obj.telegram_id)
        if obj.telegram_username:
            return obj.telegram_username
        return "—"

    @admin.display(description="TTL (sec)")
    def ttl_seconds_display(self, obj: VerificationCode) -> int:
        if obj.consumed:
            return 0
        delta = (obj.expires_at - now()).total_seconds()
        return int(delta) if delta > 0 else 0

    @admin.display(description="Created")
    def created_local(self, obj: VerificationCode) -> str:
        return localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S")

    @admin.display(description="Expires")
    def expires_local(self, obj: VerificationCode) -> str:
        return localtime(obj.expires_at).strftime("%Y-%m-%d %H:%M:%S")

    @admin.action(description="Mark selected as consumed")
    def mark_as_consumed(self, request, queryset):
        with transaction.atomic():
            updated = queryset.filter(consumed=False).update(consumed=True)
        self.message_user(
            request, f"Marked {updated} code(s) as consumed.", level=messages.SUCCESS
        )

    @admin.action(description="Purge expired (delete)")
    def purge_expired(self, request, queryset):
        n = 0
        with transaction.atomic():
            for vc in queryset:
                if vc.expires_at <= now():
                    vc.delete()
                    n += 1
        self.message_user(
            request, f"Deleted {n} expired code(s).", level=messages.WARNING
        )

    @admin.action(description="Purge old consumed (older than 7 days)")
    def purge_old_consumed(self, request, queryset):
        threshold = now() - timedelta(days=7)
        deleted, _ = VerificationCode.objects.filter(
            consumed=True, created_at__lt=threshold
        ).delete()
        self.message_user(
            request,
            f"Deleted {deleted} old consumed code(s) (created_at < {threshold:%Y-%m-%d}).",
            level=messages.INFO,
        )

    actions = ("mark_as_consumed", "purge_expired", "purge_old_consumed")
