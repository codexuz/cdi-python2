#  apps/users/views.py
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import User
from .permissions import IsSuperAdmin
from .serializers import (
    UserReadSerializer,
    UserMeUpdateSerializer,
)


@extend_schema(
    tags=["Users"],
    summary="Mening profilim (GET/PATCH)",
    responses={200: UserReadSerializer},
)
class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserMeUpdateSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        return Response(UserReadSerializer(request.user).data)

    def patch(self, request, *args, **kwargs):
        ser = self.get_serializer(
            instance=request.user, data=request.data, partial=True
        )
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(UserReadSerializer(request.user).data)


@extend_schema(
    tags=["Users"],
    summary="Foydalanuvchilar ro‘yxati (faqat superadmin)",
    parameters=[
        OpenApiParameter(
            name="q",
            description="Qidirish (fullname/phone/telegram)",
            required=False,
            type=OpenApiTypes.STR,
        ),
        OpenApiParameter(
            name="role",
            description="Filter by role",
            required=False,
            type=OpenApiTypes.STR,
            enum=["student", "teacher", "superadmin"],
        ),
        OpenApiParameter(
            name="is_active",
            description="1 yoki 0",
            required=False,
            type=OpenApiTypes.INT,
        ),
    ],
    responses={200: UserReadSerializer(many=True)},
)
class UsersListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = UserReadSerializer

    def get_queryset(self):
        qs = User.objects.all().order_by("-created_at")
        q = self.request.query_params.get("q")  # noqa
        role = self.request.query_params.get("role")  # noqa
        is_active = self.request.query_params.get("is_active")  # noqa

        if q:
            qs = qs.filter(
                Q(fullname__icontains=q)
                | Q(phone_number__icontains=q)
                | Q(telegram_username__icontains=q)
            )
        if role in {"student", "teacher", "superadmin"}:
            qs = qs.filter(role=role)
        if is_active in {"0", "1"}:
            qs = qs.filter(is_active=(is_active == "1"))
        return qs


@extend_schema(
    tags=["Users"],
    summary="Foydalanuvchi ma’lumoti (faqat superadmin)",
    responses={200: UserReadSerializer},
)
class UserDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    serializer_class = UserReadSerializer
    queryset = User.objects.all()


@extend_schema(
    tags=["Users"],
    summary="Statusni o‘zgartirish: activate/deactivate (faqat superadmin)",
    request=None,
    responses={200: UserReadSerializer},
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated, IsSuperAdmin])
def toggle_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=["is_active", "updated_at"])
    return Response(UserReadSerializer(user).data, status=status.HTTP_200_OK)
