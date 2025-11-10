# apps/speaking/services.py
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.db.models import F

from apps.profiles.models import StudentProfile
from apps.core.notifications import notify_telegram_admin_sync
from .models import SpeakingRequest


@transaction.atomic
def create_speaking_request(
    *, student: StudentProfile, note: str = ""
) -> SpeakingRequest:
    fee = Decimal(str(settings.SPEAKING.get("FEE", 0)))
    if fee <= 0:
        raise ValueError("Speaking FEE misconfigured (SPEAKING.FEE <= 0)")

    updated = StudentProfile.objects.filter(pk=student.pk, balance__gte=fee).update(
        balance=F("balance") - fee
    )
    if updated == 0:
        raise ValueError("Hisobingizda mablag' yetarli emas.")

    sr = SpeakingRequest.objects.create(
        student=student,
        fee_amount=fee,
        currency="UZS",
        note=note,
    )

    text = (
        "<b>Yangi Speaking so'rovi</b>\n"
        f"Student: <code>{student.user.fullname}</code>\n"
        f"Phone: <code>{student.user.phone_number}</code>\n"
        f"Telegram: <code>{student.user.telegram_username or '-'}</code>\n"
        f"Fee: <b>{fee} UZS</b>\n"
        f"Request ID: <code>{sr.id}</code>"
    )
    try:
        notify_telegram_admin_sync(text)
    except Exception:  # noqa
        pass

    return sr
