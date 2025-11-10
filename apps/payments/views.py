#  apps/payments/views.py
from __future__ import annotations

import hashlib
import logging
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.profiles.models import StudentProfile
from .models import Payment, PaymentStatus, PaymentProvider
from .serializers import (
    PaymentCreateSerializer,
    PaymentPublicSerializer,
    PaymentDetailSerializer,
)

log = logging.getLogger(__name__)


def verify_click_request(payload: dict) -> bool:
    secret = settings.CLICK["SECRET_KEY"]
    sign_string = (
        str(payload.get("click_trans_id", ""))
        + str(payload.get("service_id", ""))
        + str(payload.get("merchant_trans_id", ""))
        + str(payload.get("amount", ""))
        + str(payload.get("action", ""))
        + str(payload.get("sign_time", ""))
        + secret
    )
    calculated = hashlib.sha256(sign_string.encode("utf-8")).hexdigest()  # noqa
    provided = str(payload.get("sign_string", ""))
    return calculated == provided


from .services import (
    mark_payment_failed as svc_mark_payment_failed,
    mark_payment_paid_and_topup as svc_mark_payment_paid_and_topup,
)


@extend_schema(
    tags=["Payments"],
    summary="Top-up sessiya yaratish (Click redirect URL qaytaradi)",
    description=(
        "Foydalanuvchi balansini to‘ldirish uchun Payment sessiya yaratadi. "
        "`redirect_url` qaytaradi — frontend foydalanuvchini Click sahifasiga yo‘naltiradi."
    ),
    request=PaymentCreateSerializer,
    responses={201: PaymentPublicSerializer},
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_topup(request):
    ser = PaymentCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    sp = get_object_or_404(StudentProfile, user=request.user)
    amount = ser.validated_data["amount"]

    payment = Payment.objects.create(  # noqa
        student=sp,
        provider=PaymentProvider.CLICK,
        status=PaymentStatus.CREATED,
        amount=amount,
        currency="UZS",
    )

    from urllib.parse import quote_plus

    return_url = f"{settings.CLICK['RETURN_URL']}?payment_id={payment.id}"
    cancel_url = f"{settings.CLICK['CANCEL_URL']}?payment_id={payment.id}"

    redirect_url = (
        f"{settings.CLICK['BASE_URL']}"
        f"?merchant_id={settings.CLICK['MERCHANT_ID']}"
        f"&merchant_user_id={settings.CLICK['MERCHANT_USER_ID']}"
        f"&service_id={settings.CLICK.get('SERVICE_ID', '')}"
        f"&transaction={payment.id}"
        f"&amount={payment.amount}"
        f"&return_url={quote_plus(return_url)}"
        f"&cancel_url={quote_plus(cancel_url)}"
    )

    data = PaymentPublicSerializer(payment).data
    data["redirect_url"] = redirect_url
    return Response(data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Payments"],
    summary="Click webhook (prepare/check/complete/cancel)",
    description=(
        "⚠️ **FRONT uchun EMAS.**\n\n"
        "Bu endpointni faqat Click server avtomatik chaqiradi.\n"
        "Frontend hech qachon bu yerga so‘rov yubormaydi.\n\n"
        "Vazifasi: Click’dan kelgan `prepare`, `complete`, `cancel` kabi signalni qabul qilish, "
        "imzo (signature) va IP manzilini tekshirish, va to‘lov statusini yangilash."
    ),
    request={
        "application/json": {
            "example": {
                "click_trans_id": "123456789",
                "service_id": "1234",
                "merchant_trans_id": "a9b6f8b2-62d5-4c47-98d7-6a3c2f8b8f1c",
                "amount": "50000.00",
                "action": "complete",
                "error": "0",
                "error_note": "",
                "sign_time": "2025-11-06 10:20:00",
                "sign_string": "9c71a7fbe884e54c4f8b93b1d94ffb6c9c9b02f0a27b0fdf6b7a56b1a3f27d25",
            }
        }
    },
    responses={
        200: {
            "application/json": {
                "example": {
                    "status": "paid",
                    "payment_id": "a9b6f8b2-62d5-4c47-98d7-6a3c2f8b8f1c",
                }
            }
        },
        400: {"example": {"error": "Invalid signature"}},
        403: {"example": {"error": "IP not allowed"}},
    },
)
@csrf_exempt
@api_view(["POST"])
def click_webhook(request):
    allowed_ips = set(settings.CLICK.get("ALLOWED_IPS", []))
    remote_ip = request.META.get("REMOTE_ADDR", "")

    if allowed_ips and remote_ip not in allowed_ips:
        log.warning("❌ Click webhook blocked by IP: %s", remote_ip)
        return Response({"error": "IP not allowed"}, status=status.HTTP_403_FORBIDDEN)

    payload = request.data.copy()

    if not verify_click_request(payload):
        log.warning("❌ Click webhook invalid signature: %s", payload)
        return Response(
            {"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST
        )

    txn = payload.get("transaction") or payload.get("merchant_trans_id") or ""
    try:
        payment_id = UUID(str(txn))
    except (ValueError, TypeError):
        return Response(
            {"error": "Invalid transaction id"}, status=status.HTTP_400_BAD_REQUEST
        )

    action = str(payload.get("action", "")).lower()
    error = str(payload.get("error", "0"))
    error_note = payload.get("error_note", "")

    with transaction.atomic():
        payment = get_object_or_404(
            Payment.objects.select_for_update(), id=payment_id  # noqa
        )  # noqa

        if action in {"prepare", "check"}:
            if payment.status in {
                PaymentStatus.CREATED,
                PaymentStatus.FAILED,
                PaymentStatus.CANCELED,
            }:
                payment.status = PaymentStatus.PENDING
                payment.provider_invoice_id = payload.get("invoice_id", "")
                payment.provider_txn_id = payload.get("click_trans_id", "")
                payment.provider_payload = payload
                payment.error_code = error
                payment.error_note = error_note
                payment.save(
                    update_fields=[
                        "status",
                        "provider_invoice_id",
                        "provider_txn_id",
                        "provider_payload",
                        "error_code",
                        "error_note",
                        "updated_at",
                    ]
                )
            return Response({"status": "pending", "payment_id": str(payment.id)})

        if action in {"complete", "pay"}:
            if error != "0":
                svc_mark_payment_failed(
                    payment, payload, error_code=error, error_note=error_note  # noqa
                )  # noqa
                return Response({"status": "failed", "payment_id": str(payment.id)})

            try:
                svc_mark_payment_paid_and_topup(payment, payload)
            except Exception as exc:
                log.exception("❌ Top-up failed for payment %s: %s", payment.id, exc)
                svc_mark_payment_failed(payment, payload)  # noqa
                return Response(
                    {"error": "Top-up failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response({"status": "paid", "payment_id": str(payment.id)})

        if action == "cancel":
            payment.status = PaymentStatus.CANCELED
            payment.provider_payload = payload
            payment.error_code = error
            payment.error_note = error_note or "Canceled by user/provider"
            payment.save(
                update_fields=[
                    "status",
                    "provider_payload",
                    "error_code",
                    "error_note",
                    "updated_at",
                ]
            )
            return Response({"status": "canceled", "payment_id": str(payment.id)})

        return Response({"error": "Unknown action"}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Payments"],
    summary="Payment status (frontend polling uchun)",
    description="Frontend Click sahifasidan qaytgach, payment_id orqali statusni tekshiradi.",
    parameters=[
        OpenApiParameter(
            name="payment_id",
            type=OpenApiTypes.UUID,
            location="query",
            description="Payment ID (uuid)",
        ),
    ],
    responses={200: PaymentDetailSerializer},
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def payment_status(request):
    pid = request.query_params.get("payment_id")
    payment = get_object_or_404(Payment, id=pid, student__user=request.user)
    return Response(PaymentDetailSerializer(payment).data)
