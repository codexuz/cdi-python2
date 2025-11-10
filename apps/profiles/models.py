# apps/profiles/models.py
from decimal import Decimal

from django.conf import settings

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.users.models import User, UUIDPrimaryKeyMixin, TimeStampedMixin


class StudentProfile(UUIDPrimaryKeyMixin, TimeStampedMixin):
    TYPE_ONLINE = "online"
    TYPE_OFFLINE = "offline"
    TYPE_CHOICES = [(TYPE_ONLINE, "Online"), (TYPE_OFFLINE, "Offline")]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile", unique=True
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="UZS-like fixed precision; non-negative.",
    )
    is_approved = models.BooleanField(default=False, db_index=True)

    type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default=TYPE_ONLINE, db_index=True
    )

    class Meta:
        db_table = "student_profiles"
        indexes = [
            models.Index(fields=["is_approved"], name="studprof_approved_idx"),
            models.Index(fields=["type"], name="studprof_type_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(balance__gte=0),
                name="studprof_balance_gte_0",
            ),
            models.CheckConstraint(
                check=(
                    (Q(is_approved=True) & Q(type="offline"))
                    | (Q(is_approved=False) & Q(type="online"))
                ),
                name="studprof_type_matches_approval",
            ),
        ]

    def save(self, *args, **kwargs):
        self.type = self.TYPE_OFFLINE if self.is_approved else self.TYPE_ONLINE
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"StudentProfile<{self.user_id}> {self.type} | bal={self.balance}"  # type: ignore[attr-defined]


class TeacherProfile(UUIDPrimaryKeyMixin, TimeStampedMixin):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="teacher_profile", unique=True
    )

    class Meta:
        db_table = "teacher_profiles"
        indexes = [models.Index(fields=["created_at"], name="teachprof_created_idx")]

    def __str__(self) -> str:
        return f"TeacherProfile<{self.user_id}>"  # type: ignore[attr-defined]


class StudentApprovalLog(UUIDPrimaryKeyMixin, TimeStampedMixin):

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="approval_logs"
    )
    approved = models.BooleanField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="student_approval_actions",
    )
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "student_approval_logs"
        indexes = [
            models.Index(fields=["created_at"], name="studapprlog_created_idx"),
            models.Index(fields=["approved"], name="studapprlog_approved_idx"),
        ]

    def __str__(self) -> str:
        who = self.actor.fullname if self.actor else "system"
        return f"ApprovalLog<{self.student_id}> approved={self.approved} by {who}"  # type: ignore[attr-defined]


class StudentTopUpLog(UUIDPrimaryKeyMixin, TimeStampedMixin):

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="topup_logs"
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    new_balance = models.DecimalField(max_digits=12, decimal_places=2)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="student_topup_actions",
    )
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "student_topup_logs"
        indexes = [
            models.Index(fields=["created_at"], name="studtopuplog_created_idx"),
        ]

    def __str__(self) -> str:
        who = self.actor.fullname if self.actor else "system"
        return f"TopUpLog<{self.student_id}> +{self.amount} by {who}, new={self.new_balance}"  # type: ignore[attr-defined]
