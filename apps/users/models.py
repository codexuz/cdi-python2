# apps/users/models.py
import re
import uuid
from typing import Optional

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
    Group,
    Permission,
)
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone


class UUIDPrimaryKeyMixin(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedMixin(models.Model):

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    phone_validator = RegexValidator(
        regex=r"^\+?[1-9]\d{7,14}$",
        message="Phone must be in international format, e.g. +998901234567",
    )

    tg_username_re = re.compile(r"^[A-Za-z0-9_]{5,32}$")

    def _normalize_phone(self, phone: str) -> str:
        phone = (phone or "").strip().replace(" ", "").replace("-", "")
        self.phone_validator(phone)
        return phone

    def _normalize_tg_username(self, username: Optional[str]) -> Optional[str]:
        if not username:
            return None
        username = username.strip().lstrip("@").lower()
        if not self.tg_username_re.match(username):
            raise ValueError(
                "Invalid Telegram username (5-32 chars, letters/digits/_)."
            )
        return username

    def create_user(
        self,
        fullname: str,
        phone_number: str,
        role: str,
        password: Optional[str] = None,
        telegram_username: Optional[str] = None,
        **extra_fields,
    ):
        if not fullname:
            raise ValueError("Fullname is required")
        if not phone_number:
            raise ValueError("Phone number is required")
        if role not in {"superadmin", "student", "teacher"}:
            raise ValueError("Invalid role")

        user = self.model(
            fullname=fullname.strip(),
            phone_number=self._normalize_phone(phone_number),
            role=role,
            telegram_username=self._normalize_tg_username(telegram_username),
            **extra_fields,
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        fullname: str,
        phone_number: str,
        password: Optional[str] = None,
        **extra_fields,
    ):
        extra_fields.pop("role", None)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(
            fullname=fullname,
            phone_number=phone_number,
            role="superadmin",
            password=password,
            **extra_fields,
        )


class User(UUIDPrimaryKeyMixin, TimeStampedMixin, AbstractBaseUser, PermissionsMixin):
    class Roles(models.TextChoices):
        SUPERADMIN = "superadmin", "Superadmin"
        STUDENT = "student", "Student"
        TEACHER = "teacher", "Teacher"

    fullname = models.CharField(max_length=100)

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    telegram_username = models.CharField(
        max_length=50,
        unique=False,
        null=True,
        blank=True,
        help_text="Stored lowercased; unique (case-insensitive) when not null.",
    )

    phone_number = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=Roles.choices)  # noqa

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    last_activity = models.DateTimeField(null=True, blank=True, db_index=True)

    groups = models.ManyToManyField(Group, related_name="cdi_users", blank=True)
    user_permissions = models.ManyToManyField(
        Permission, related_name="cdi_user_perms", blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["fullname"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone_number"], name="users_phone_idx"),
            models.Index(fields=["role"], name="users_role_idx"),
            models.Index(fields=["telegram_id"], name="users_tgid_idx"),
            models.Index(fields=["created_at"], name="users_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(phone_number__regex=r"^\+?[1-9]\d{7,14}$"),
                name="users_phone_e164_like",
            ),
            models.CheckConstraint(
                check=~models.Q(fullname=""),
                name="users_fullname_not_empty",
            ),
            models.UniqueConstraint(
                Lower("telegram_username"),
                name="users_tg_username_ci_uniq",
                condition=Q(telegram_username__isnull=False),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.fullname} ({self.phone_number})"

    def save(self, *args, **kwargs):
        if self.telegram_username:
            self.telegram_username = self.telegram_username.strip().lstrip("@").lower()
        return super().save(*args, **kwargs)

    def update_last_activity(self):
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])
