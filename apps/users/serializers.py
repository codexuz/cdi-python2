#  apps/users/serializers.py
from typing import Optional

from django.core.validators import RegexValidator
from django.db.models.functions import Lower
from rest_framework import serializers

from .models import User

_phone_validator = RegexValidator(
    regex=r"^\+?[1-9]\d{7,14}$",
    message="Phone must be in international format, e.g. +998901234567",
)


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "fullname",
            "telegram_id",
            "telegram_username",
            "phone_number",
            "role",
            "is_active",
            "last_activity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class UserMeUpdateSerializer(serializers.ModelSerializer):
    telegram_username = serializers.CharField(
        allow_null=True, allow_blank=True, required=False, max_length=50
    )

    class Meta:
        model = User
        fields = ["fullname", "telegram_username"]

    def validate_telegram_username(self, v: Optional[str]):
        if not v:
            return None

        v = v.strip().lstrip("@").lower()

        if not User.objects.tg_username_re.match(v):
            raise serializers.ValidationError(
                "Invalid Telegram username (5-32 chars, letters/digits/_)."
            )

        qs = User.objects.all()
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.filter(telegram_username__iexact=v).exists():
            raise serializers.ValidationError("Telegram username already taken.")

        return v


class AdminUserWriteSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(validators=[_phone_validator])

    class Meta:
        model = User
        fields = [
            "fullname",
            "telegram_username",
            "phone_number",
            "role",
            "is_active",
        ]

    def validate_telegram_username(self, v: Optional[str]):
        if not v:
            return None
        v = v.strip().lstrip("@").lower()
        if not User.objects.tg_username_re.match(v):
            raise serializers.ValidationError(
                "Invalid Telegram username (5-32 chars, letters/digits/_)."
            )
        qs = (
            User.objects.exclude(pk=self.instance.pk)
            if self.instance
            else User.objects.all()
        )
        if qs.filter(Lower("telegram_username") == v).exists():
            raise serializers.ValidationError("Telegram username already taken.")
        return v
