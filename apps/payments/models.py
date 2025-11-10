# apps/payments/models.py
import uuid

from django.db import models
from django.utils import timezone

from apps.profiles.models import StudentProfile


class PaymentProvider(models.TextChoices):
    CLICK = "click", "Click"


class PaymentStatus(models.TextChoices):
    CREATED = "created", "Created"
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"
    CANCELED = "canceled", "Canceled"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="payments"
    )
    provider = models.CharField(
        max_length=20,
        choices=PaymentProvider.choices,
        default=PaymentProvider.CLICK,  # noqa
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,  # noqa
        default=PaymentStatus.CREATED,
        db_index=True,
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="UZS")

    provider_invoice_id = models.CharField(
        max_length=64, blank=True, default="", db_index=True
    )
    provider_txn_id = models.CharField(
        max_length=64, blank=True, default="", db_index=True
    )

    idempotency_key = models.CharField(
        max_length=64, blank=True, default="", db_index=True
    )
    provider_payload = models.JSONField(default=dict, blank=True)  # webhook raw

    error_code = models.CharField(max_length=20, blank=True, default="")
    error_note = models.TextField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payments"
        indexes = [
            models.Index(fields=["student", "status"], name="pay_student_status_idx"),
            models.Index(fields=["created_at"], name="pay_created_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_txn_id"],
                name="uniq_provider_txn",
                condition=~models.Q(provider_txn_id=""),
            )
        ]

    def __str__(self):
        return f"Payment<{self.id}> {self.provider} {self.status} {self.amount} {self.currency}"
