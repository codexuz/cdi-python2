#  apps.accounts views
from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics, status, throttling, permissions, serializers
from rest_framework.response import Response

from apps.accounts.models import VerificationCode
from .serializers import (
    RegisterStartSerializer,
    RegisterVerifySerializer,
    LoginVerifySerializer,
    OtpIngestSerializer,
)
from .services import issue_tokens


class OTPIngestThrottle(throttling.UserRateThrottle):
    scope = "otp_ingest"


class OTPVerifyThrottle(throttling.UserRateThrottle):
    scope = "otp_verify"


class OTPStatusThrottle(throttling.UserRateThrottle):
    scope = "otp_status"


@extend_schema(
    tags=["accounts"],
    summary="Register start",
    description=(
        "Foydalanuvchini yaratadi (users). Role bo‘yicha profil signal orqali **auto** yaratiladi:\n"
        "- student → StudentProfile(balance=0, is_approved=False → type=online)\n"
        "- teacher → TeacherProfile\n\n"
        "Keyingi bosqich: Telegram botdan kod olib `/api/accounts/register/verify/` da tekshirish."
    ),
    request=RegisterStartSerializer,
    responses={
        201: OpenApiResponse(
            response=dict, description='{"message": "...", "user_id": "<uuid>"}'
        ),
        400: OpenApiResponse(description="Validation error"),
    },
)
class RegisterStartView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterStartSerializer
    throttle_classes = [OTPVerifyThrottle]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(
            {
                "message": "User created. Verify with Telegram code.",
                "user_id": str(user.id),
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["accounts"],
    summary="Register verify (Telegram OTP)",
    description=(
        "Bot yuborgan **register** purpose’dagi kodni tekshiradi.\n"
        "Muvaffaqiyatli bo‘lsa, `user.telegram_id`/`telegram_username` ni bind qiladi va JWT qaytaradi."
    ),
    request=RegisterVerifySerializer,
    responses={
        200: OpenApiResponse(
            response=dict,
            description='{"message":"Registration completed.","access":"...","refresh":"..."}',
        ),
        400: OpenApiResponse(description="Invalid/expired code yoki binding xatosi"),
    },
)
class RegisterVerifyView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterVerifySerializer
    throttle_classes = [OTPVerifyThrottle]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        tokens = issue_tokens(user)
        return Response(
            {"message": "Registration completed.", **tokens}, status=status.HTTP_200_OK
        )


@extend_schema(
    tags=["accounts"],
    summary="Login verify (Telegram OTP)",
    description="Faqat Telegram OTP orqali login (body’da `code` va **`telegram_id`** bo‘lishi shart).",
    request=LoginVerifySerializer,
    responses={
        200: OpenApiResponse(
            response=dict,
            description='{"message":"Login success.","access":"...","refresh":"..."}',
        ),
        400: OpenApiResponse(description="Invalid/expired code yoki user topilmadi"),
    },
)
class LoginVerifyView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginVerifySerializer
    throttle_classes = [OTPVerifyThrottle]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        tokens = issue_tokens(user)
        return Response(
            {"message": "Login success.", **tokens}, status=status.HTTP_200_OK
        )


@extend_schema(
    tags=["accounts"],
    summary="OTP ingest (Bot → Backend)",
    description=(
        "⚠️ **FRONTEND uchun emas!**\n\n"
        "Ushbu endpoint faqat **Telegram bot** tomonidan OTP (tasdiqlash kodi) yuborish uchun ishlatiladi. "
        "Kod yuborilgan paytdan boshlab **2 daqiqa** davomida amal qiladi.\n\n"
        "**Xavfsizlik**: So‘rov faqat `X-Bot-Token` header orqali yuborilgan **shared-secret** token bilan "
        "tasdiqlangan bo‘lishi shart."
    ),
    request=OtpIngestSerializer,
    parameters=[
        OpenApiParameter(
            name="X-Bot-Token",
            type=str,
            location="header",
            required=True,
            description="Shared secret (settings.TELEGRAM_BOT_INGEST_TOKEN)",
        )
    ],
    responses={
        201: OpenApiResponse(
            response=dict, description='{"status":"stored","expires_at":"..."}'
        ),
        409: OpenApiResponse(description="Active code exists"),
        401: OpenApiResponse(description="Unauthorized"),
        400: OpenApiResponse(description="Validation error"),
    },
)
class OtpIngestView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = OtpIngestSerializer
    throttle_classes = [OTPIngestThrottle]

    def create(self, request, *args, **kwargs):
        expected = getattr(settings, "TELEGRAM_BOT_INGEST_TOKEN", None)
        provided = request.headers.get("X-Bot-Token")
        if expected and provided != expected:
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        ser = self.get_serializer(data=request.data)
        try:
            ser.is_valid(raise_exception=True)
            vc = ser.save()
        except serializers.ValidationError as e:
            if getattr(e, "code", None) == "conflict" or (
                isinstance(e.detail, dict)
                and e.detail.get("detail") == "Active code exists"
            ):
                data = (
                    e.detail
                    if isinstance(e.detail, dict)
                    else {"detail": "Active code exists"}
                )
                return Response(data, status=status.HTTP_409_CONFLICT)
            raise

        return Response(
            {"status": "stored", "expires_at": vc.expires_at},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["accounts"],
    summary="OTP status (Bot → Backend)",
    description=(
        "⚠️ **FRONTEND uchun emas!**\n\n"
        "Ushbu endpoint faqat **Telegram bot** tomonidan OTP holatini "
        "(faol/eskirgan) tekshirish uchun ishlatiladi.\n\n"
        "So‘rovda `telegram_id` yoki `telegram_username`, hamda `purpose` (`register` | `login`) "
        "bo‘lishi kerak.\n\n"
        "**Xavfsizlik**: `X-Bot-Token` header orqali yuborilgan **shared-secret** bilan "
        "autentifikatsiya qilinadi."
    ),
    parameters=[
        OpenApiParameter(
            name="X-Bot-Token",
            type=str,
            location="header",
            required=True,
            description="Shared secret (settings.TELEGRAM_BOT_INGEST_TOKEN)",
        ),
        OpenApiParameter(
            name="telegram_id",
            type=int,
            location="query",
            required=False,
        ),
        OpenApiParameter(
            name="telegram_username",
            type=str,
            location="query",
            required=False,
        ),
        OpenApiParameter(
            name="purpose",
            type=str,
            location="query",
            required=True,
            description="register | login",
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=dict,
            description='{"active":true,"expires_at":"...","ttl_seconds":73} yoki {"active":false}',
        ),
        401: OpenApiResponse(description="Unauthorized"),
        400: OpenApiResponse(description="Validation error"),
    },
)
class OtpStatusView(generics.GenericAPIView):

    permission_classes = [permissions.AllowAny]
    throttle_classes = [OTPStatusThrottle]

    def get(self, request, *args, **kwargs):  # noqa yoki
        telegram_id = request.query_params.get("telegram_id")
        telegram_username = request.query_params.get("telegram_username")
        purpose = request.query_params.get("purpose")

        if not purpose:
            return Response(
                {"detail": "purpose is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vc = VerificationCode.objects.latest_alive_for(
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            purpose=purpose,
        )

        if not vc:
            return Response(
                {"active": False, "remaining_seconds": 0},
                status=status.HTTP_200_OK,
            )

        remaining = int((vc.expires_at - timezone.now()).total_seconds())
        return Response(
            {
                "active": True,
                "remaining_seconds": max(remaining, 0),
            },
            status=status.HTTP_200_OK,
        )
