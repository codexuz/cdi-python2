#  apps/user_tests/services.py
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.profiles.models import StudentProfile
from apps.tests.models.ielts import Test
from .models import UserTest


@transaction.atomic
def purchase_test(*, user, test: Test) -> UserTest:
    sp = getattr(user, "student_profile", None)
    if not sp:
        raise ValidationError("Student profile mavjud emas")

    price = (
        Decimal(getattr(test, "price", 0))
        if sp.type == StudentProfile.TYPE_ONLINE
        else Decimal("0.00")
    )

    ut, created = UserTest.objects.get_or_create(
        user=user, test=test, defaults={"price_paid": price}
    )
    if not created:
        return ut  # allaqachon sotib olingan

    if price > 0:
        # concurrency-safe balansni tekshirish
        sp = StudentProfile.objects.select_for_update().get(pk=sp.pk)
        if sp.balance < price:
            raise ValidationError("Balance yetarli emas!")
        sp.balance -= price
        sp.save(update_fields=["balance"])

    return ut
