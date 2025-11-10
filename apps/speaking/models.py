#  app/models/speaking.py
from django.db import models

from apps.profiles.models import StudentProfile
from apps.users.models import UUIDPrimaryKeyMixin, TimeStampedMixin


class SpeakingRequest(UUIDPrimaryKeyMixin, TimeStampedMixin):

    STATUS_CREATED = "created"
    STATUS_CHOICES = [(STATUS_CREATED, "Created")]

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="speaking_requests"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, db_index=True
    )

    fee_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="UZS")
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "speaking_requests"
        indexes = [
            models.Index(fields=["student", "status"], name="spreq_student_status_idx"),
            models.Index(fields=["created_at"], name="spreq_created_idx"),
        ]

    def __str__(self) -> str:
        return f"SpeakingRequest<{self.id}> {self.student_id} {self.fee_amount} {self.currency}"  # type: ignore[attr-defined]
