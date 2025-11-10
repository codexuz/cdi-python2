# apps/payments/services.py
import hashlib
import hmac
from decimal import Decimal
from typing import Dict, Any

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.profiles.models import StudentProfile, StudentTopUpLog
from .models import Payment, PaymentStatus


def _click_sign(payload: Dict[str, Any]) -> str:
    secret = settings.CLICK["SECRET_KEY"].encode()
    base = (
        f"{payload.get('merchant_id', '')}"
        f"{payload.get('amount', '')}"
        f"{payload.get('transaction', '')}"
        f"{payload.get('action', '')}"
    ).encode()
    return hmac.new(secret, base, hashlib.md5).hexdigest()


def verify_click_request(payload: Dict[str, Any]) -> bool:

    provided = (payload.get("sign") or "").lower().strip()
    expected = _click_sign(payload)
    return provided == expected


@transaction.atomic
def mark_payment_paid_and_topup(
    *, payment: Payment, webhook_payload: Dict[str, Any]
) -> Payment:

    if payment.status == PaymentStatus.PAID:
        return payment
    amount = Decimal(str(payment.amount))

    StudentProfile.objects.filter(pk=payment.student.pk).update(
        balance=F("balance") + amount
    )

    payment.student.refresh_from_db(fields=["balance"])

    StudentTopUpLog.objects.create(
        student=payment.student,
        amount=amount,
        new_balance=payment.student.balance,
        actor=None,
        note=f"Click top-up Payment<{payment.id}>",
    )

    payment.status = PaymentStatus.PAID
    payment.provider_payload = webhook_payload or {}
    payment.completed_at = timezone.now()
    payment.save(
        update_fields=[
            "status",
            "provider_payload",
            "completed_at",
            "updated_at",
        ]
    )

    return payment


def mark_payment_failed(
    *,
    payment: Payment,
    webhook_payload: Dict[str, Any],
    error_code: str | None = None,
    error_note: str | None = None,
) -> Payment:

    payment.status = PaymentStatus.FAILED
    payment.provider_payload = webhook_payload or {}

    error_code = error_code or str(webhook_payload.get("error", "") or "")
    error_note = error_note or webhook_payload.get("error_note", "")

    if error_code:
        payment.error_code = error_code
    if error_note:
        payment.error_note = error_note

    update_fields = ["status", "provider_payload", "updated_at"]
    if error_code:
        update_fields.append("error_code")
    if error_note:
        update_fields.append("error_note")

    payment.save(update_fields=update_fields)
    return payment
