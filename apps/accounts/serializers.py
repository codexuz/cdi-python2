# apps/accounts/serializers.py
from __future__ import annotations
from __future__ import annotations
from django.utils import timezone
from typing import Any, Dict
from uuid import UUID

from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import VerificationCode
from apps.users.models import User


class DjangoValidationError:
    def __init__(self, message: str):
        self.message = message


class RegisterStartSerializer(serializers.Serializer):
    fullname = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=20)
    role = serializers.ChoiceField(
        choices=[(User.Roles.STUDENT, "student"), (User.Roles.TEACHER, "teacher")]
    )

    def validate(self, attrs):
        raw = attrs["phone_number"]
        phone = (raw or "").strip()
        for ch in (" ", "-", "(", ")"):
            phone = phone.replace(ch, "")
        try:
            User.objects.phone_validator(phone)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"phone_number": e.message})
        if User.objects.filter(phone_number=phone).exists():
            raise serializers.ValidationError(
                {"phone_number": "This phone number is already registered."}
            )
        attrs["phone_number"] = phone
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class RegisterVerifySerializer(serializers.Serializer):

    user_id = serializers.UUIDField()
    code = serializers.CharField(max_length=6)

    @staticmethod
    def _load_user(user_id: UUID) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist as exc:  # noqa
            raise serializers.ValidationError("User not found.") from exc

    @staticmethod
    def _load_vc_by_code(code: str) -> VerificationCode | None:
        return (
            VerificationCode.objects.alive()
            .filter(code=code, purpose=VerificationCode.Purpose.REGISTER)
            .order_by("-created_at")
            .first()
        )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        user = self._load_user(attrs["user_id"])
        vc = self._load_vc_by_code(attrs["code"])
        if not vc or not vc.is_valid(attrs["code"]):
            raise serializers.ValidationError("Invalid or expired code.")

        if (
            vc.telegram_id
            and User.objects.filter(telegram_id=vc.telegram_id)
            .exclude(id=user.id)
            .exists()
        ):
            raise serializers.ValidationError(
                "This Telegram is already bound to another user."
            )

        attrs["user"] = user
        attrs["vc"] = vc
        return attrs

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> User:
        user: User = validated_data["user"]
        vc: VerificationCode = validated_data["vc"]

        if vc.telegram_id:
            user.telegram_id = vc.telegram_id
        if vc.telegram_username and not user.telegram_username:
            user.telegram_username = (
                (vc.telegram_username or "").strip().lstrip("@").lower()
            )

        user.save(update_fields=["telegram_id", "telegram_username", "updated_at"])
        vc.consume()
        return user


class LoginVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        code = attrs["code"]

        vc = (
            VerificationCode.objects.filter(
                purpose=VerificationCode.Purpose.LOGIN,
                consumed=False,
                expires_at__gt=timezone.now(),
                code=code,
            )
            .order_by("-created_at")
            .first()
        )

        if not vc or not vc.is_valid(code):
            raise serializers.ValidationError("Invalid or expired code.")

        user = User.objects.filter(telegram_id=vc.telegram_id).first()
        if not user:
            raise serializers.ValidationError("User not linked to this Telegram ID.")

        attrs["user"] = user
        attrs["vc"] = vc
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        vc: VerificationCode = validated_data["vc"]
        vc.consume()
        return validated_data["user"]


class OtpIngestSerializer(serializers.Serializer):

    telegram_id = serializers.IntegerField(required=False)
    telegram_username = serializers.CharField(required=False, allow_blank=True)
    code = serializers.CharField(max_length=6)
    purpose = serializers.ChoiceField(choices=VerificationCode.Purpose.choices)  # type: ignore

    @staticmethod
    def validate_code(v: str) -> str:
        if len(v) != 6 or not v.isdigit():
            raise serializers.ValidationError("Code must be 6 digits.")
        return v

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> VerificationCode:
        # username normalize
        tuser = validated_data.get("telegram_username") or None
        if tuser:
            tuser = tuser.strip().lstrip("@").lower()
            validated_data["telegram_username"] = tuser

        exists = VerificationCode.objects.has_active(
            telegram_id=validated_data.get("telegram_id"),
            telegram_username=validated_data.get("telegram_username"),
            purpose=validated_data["purpose"],
        )
        if exists:
            raise serializers.ValidationError(
                {"detail": "Active code exists", "expires_at": exists.expires_at},
                code="conflict",
            )

        return VerificationCode.objects.issue(**validated_data, ttl_minutes=2)


class OtpStatusQuerySerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField(required=False)
    telegram_username = serializers.CharField(required=False, allow_blank=True)
    purpose = serializers.ChoiceField(choices=VerificationCode.Purpose.choices)  # type: ignore

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if not attrs.get("telegram_id") and not attrs.get("telegram_username"):
            raise serializers.ValidationError(
                "telegram_id or telegram_username is required."
            )

        if attrs.get("telegram_username"):
            attrs["telegram_username"] = (
                attrs["telegram_username"].strip().lstrip("@").lower()
            )
        return attrs
