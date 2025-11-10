# apps/user_tests/views.py
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tests.models.ielts import Test
from .models import UserTest, TestResult
from .serializers import (
    TestListItemSerializer,
    UserTestSerializer,
    TestResultSerializer,
)
from .services import purchase_test


@extend_schema(
    tags=["UserTests"],
    summary="Barcha testlar (purchased flag bilan)",
    responses={200: TestListItemSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def all_tests(request):
    purchased_qs = UserTest.objects.filter(user=request.user, test=OuterRef("pk"))
    tests = (
        Test.objects.all()
        .annotate(purchased=Exists(purchased_qs))
        .order_by("-created_at")
    )
    return Response(TestListItemSerializer(tests, many=True).data)


@extend_schema(
    tags=["UserTests"],
    summary="Test sotib olish (balansdan yechish)",
    parameters=[
        OpenApiParameter(
            name="test_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,  # noqa
            description="Sotib olinadigan test ID-si",
            required=True,
        )
    ],
    responses={201: UserTestSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def purchase_test_api(request, test_id: int):
    user = request.user
    test = get_object_or_404(Test, pk=test_id)

    if UserTest.objects.filter(user=user, test=test).exists():
        return Response({"detail": "Already purchased"}, status=400)

    try:
        ut = purchase_test(user=user, test=test)
    except Exception as e:
        return Response({"error": str(e)}, status=400)

    return Response(UserTestSerializer(ut).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["UserTests"],
    summary="Mening sotib olingan testlarim (My tests)",
    responses={200: UserTestSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_tests(request):
    uts = (
        UserTest.objects.filter(user=request.user)
        .select_related("test")
        .order_by("-created_at")
    )
    return Response(UserTestSerializer(uts, many=True).data)


@extend_schema(
    tags=["UserTests"],
    summary="Mening natijalarim (Result reviews)",
    responses={200: TestResultSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_results(request):
    results = (
        TestResult.objects.filter(user_test__user=request.user)
        .select_related("user_test__test")
        .order_by("-created_at")
    )
    return Response(TestResultSerializer(results, many=True).data)
