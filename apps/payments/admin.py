# apps/payments/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "amount",
        "currency",
        "status",
        "provider",
        "provider_invoice_id",
        "provider_txn_id",
        "created_at",
        "completed_at",
    )
    list_filter = (
        "status",
        "provider",
        "currency",
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = (
        "id",
        "student__user__fullname",
        "student__user__email",
        "provider_txn_id",
        "provider_invoice_id",
    )
    readonly_fields = (
        "id",
        "created_at",
        "completed_at",
        "provider_txn_id",
        "provider_invoice_id",
    )
    raw_id_fields = ("student",)
    list_per_page = 30
    ordering = ("-created_at",)

    fieldsets = (
        (
            _("Transaction Info"),
            {
                "fields": (
                    "student",
                    "amount",
                    "currency",
                    "status",
                    "provider",
                )
            },
        ),
        (
            _("Provider Details"),
            {
                "classes": ("collapse",),
                "fields": (
                    "provider_txn_id",
                    "provider_invoice_id",
                ),
            },
        ),
        (
            _("Timestamps"),
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "completed_at",
                ),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Payment.objects.get(pk=obj.pk)
            if obj.status == "completed" and old_obj.status != "completed":
                obj.completed_at = timezone.now()
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False
