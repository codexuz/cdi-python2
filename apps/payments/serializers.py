# apps/payments/serializers.py
from django.conf import settings
from rest_framework import serializers

from .models import Payment, PaymentStatus


class PaymentCreateSerializer(serializers.Serializer):

    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="To‘lov summasi (UZS)",
        min_value=0.01,
    )

    def validate_amount(self, v):  # noqa
        min_amt = settings.PAYMENTS["MIN_TOPUP"]
        max_amt = settings.PAYMENTS["MAX_TOPUP"]

        if v < min_amt:
            raise serializers.ValidationError(f"Minimal summa {min_amt} UZS.")
        if v > max_amt:
            raise serializers.ValidationError(f"Maksimal summa {max_amt} UZS.")
        return v


class PaymentPublicSerializer(serializers.ModelSerializer):
    redirect_url = serializers.URLField(
        read_only=True, help_text="Click to‘lov sahifasi URL manzili"
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "amount",
            "currency",
            "created_at",
            "completed_at",
            "redirect_url",
        ]
        read_only_fields = fields


class PaymentDetailSerializer(serializers.ModelSerializer):

    student = serializers.UUIDField(source="student.id", read_only=True)
    is_paid = serializers.SerializerMethodField(
        help_text="To‘lov muvaffaqiyatli yakunlangani (true/false)"
    )

    def get_is_paid(self, obj: Payment) -> bool:  # noqa
        return obj.status == PaymentStatus.PAID

    class Meta:
        model = Payment
        fields = [
            "id",
            "student",
            "provider",
            "status",
            "is_paid",
            "amount",
            "currency",
            "provider_invoice_id",
            "provider_txn_id",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields
