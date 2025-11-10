# apps/accounts/models.py
from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Optional

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone


class VerificationCodeQuerySet(models.QuerySet):
    def alive(self) -> "VerificationCodeQuerySet":
        now = timezone.now()
        return self.filter(consumed=False, expires_at__gt=now)  # type: ignore

    def for_target(
        self,
        *,
        telegram_id: Optional[int] = None,
        telegram_username: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> "VerificationCodeQuerySet":
        qs = self
        if telegram_id is not None:
            qs = qs.filter(telegram_id=telegram_id)
        if telegram_username is not None:
            qs = qs.filter(telegram_username=telegram_username)
        if purpose is not None:
            qs = qs.filter(purpose=purpose)
        return qs

    def latest_alive_for(
        self,
        *,
        telegram_id: Optional[int] = None,
        telegram_username: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> Optional["VerificationCode"]:
        return (
            self.alive()
            .for_target(
                telegram_id=telegram_id,
                telegram_username=telegram_username,
                purpose=purpose,
            )
            .order_by("-created_at")
            .first()
        )


class VerificationCodeManager(models.Manager.from_queryset(VerificationCodeQuerySet)):
    def issue(
        self,
        *,
        telegram_id: Optional[int],
        telegram_username: Optional[str],
        code: str,
        purpose: str,
        ttl_minutes: int = 2,
    ) -> "VerificationCode":

        expires = timezone.now() + timedelta(minutes=ttl_minutes)
        return self.create(  # type: ignore
            telegram_id=telegram_id,
            telegram_username=(telegram_username or None),
            code=code,
            purpose=purpose,
            expires_at=expires,
        )

    def has_active(
        self,
        *,
        telegram_id: Optional[int],
        telegram_username: Optional[str],
        purpose: str,
    ) -> Optional["VerificationCode"]:
        return self.latest_alive_for(
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            purpose=purpose,
        )


class VerificationCode(models.Model):
    class Purpose(models.TextChoices):
        REGISTER = "register", "Register"
        LOGIN = "login", "Login"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    telegram_id = models.BigIntegerField(db_index=True, null=True)
    telegram_username = models.CharField(
        max_length=50, null=True, blank=True, db_index=True
    )

    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=10, choices=Purpose.choices)  # type: ignore

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    consumed = models.BooleanField(default=False, db_index=True)

    from typing import ClassVar

    objects: ClassVar[VerificationCodeManager] = VerificationCodeManager()

    class Meta:
        db_table = "verification_codes"
        indexes = [
            models.Index(
                fields=[
                    "telegram_id",
                    "purpose",
                    "consumed",
                    "expires_at",
                    "created_at",
                ],
                name="vc_tid_purp_cons_exp_cre_idx",
            ),
            models.Index(
                fields=[
                    "telegram_username",
                    "purpose",
                    "consumed",
                    "expires_at",
                    "created_at",
                ],
                name="vc_tuser_purp_cons_exp_cre_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(code__regex=r"^\d{6}$"),
                name="verification_code_six_digits",
            ),
        ]

    def is_valid(self, raw_code: str) -> bool:
        now = timezone.now()
        return (
            (not self.consumed) and (self.code == raw_code) and (now < self.expires_at)
        )

    @transaction.atomic
    def consume(self) -> None:
        if not self.consumed:
            self.consumed = True
            self.save(update_fields=["consumed"])
