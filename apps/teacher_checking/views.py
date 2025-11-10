#  apps/teacher_checking/views.py
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.profiles.permissions import IsTeacherOrSuperAdmin
from apps.user_tests.models import UserTest
from .models import TeacherSubmission
from .serializers import (
    TeacherSubmissionSerializer,
    SubmissionCreateSerializer,
    ClaimSerializer,
    GradeSerializer,
)
from .services import submit_writing, claim_submission, grade_submission


@extend_schema(
    tags=["Teacher Checking"], summary="Student submit writing (Task1/Task2)"
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def student_submit_writing(request):
    ser = SubmissionCreateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    ut = get_object_or_404(
        UserTest, id=ser.validated_data["user_test_id"], user=request.user
    )
    sub = submit_writing(
        user_test=ut, task=ser.validated_data["task"], text=ser.validated_data["text"]
    )
    return Response(
        TeacherSubmissionSerializer(sub).data, status=status.HTTP_201_CREATED
    )


@extend_schema(tags=["Teacher Checking"], summary="All Writing (pool) — requested")
class AllWritingList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrSuperAdmin]
    serializer_class = TeacherSubmissionSerializer

    def get_queryset(self):
        return (
            TeacherSubmission.objects.filter(status=TeacherSubmission.Status.REQUESTED)
            .select_related("user_test__user", "user_test__test", "teacher")
            .order_by("submitted_at")
        )


@extend_schema(tags=["Teacher Checking"], summary="My Checking — in_checking")
class MyCheckingList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrSuperAdmin]
    serializer_class = TeacherSubmissionSerializer

    def get_queryset(self):
        return (
            TeacherSubmission.objects.filter(
                status=TeacherSubmission.Status.IN_CHECKING, teacher=self.request.user
            )
            .select_related("user_test__user", "user_test__test", "teacher")
            .order_by("-updated_at")
        )


@extend_schema(tags=["Teacher Checking"], summary="Checked — by me")
class MyCheckedList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrSuperAdmin]
    serializer_class = TeacherSubmissionSerializer

    def get_queryset(self):
        return (
            TeacherSubmission.objects.filter(
                status=TeacherSubmission.Status.CHECKED, teacher=self.request.user
            )
            .select_related("user_test__user", "user_test__test", "teacher")
            .order_by("-checked_at")
        )


@extend_schema(
    tags=["Teacher Checking"],
    summary="Claim one submission (safe lock)",
    description=(
        "⚠️ **INTERNAL API — NOT for frontend use!**\n\n"
        "Bu endpoint backend tizim tomonidan submission’ni xavfsiz tarzda "
        "teacher’ga biriktirish (safe lock) uchun ishlatiladi.\n\n"
        "- Maqsad: bir nechta teacher bir vaqtning o‘zida bitta submission’ni "
        "tekshirishni boshlamasligi uchun.\n"
        "- Agar submission allaqachon boshqa teacher tomonidan olingan bo‘lsa, "
        "xato qaytariladi (`already claimed`).\n"
        "- Faqat `Teacher` yoki `SuperAdmin` rollarida ishlaydi.\n\n"
        "**Frontend tomonidan to‘g‘ridan-to‘g‘ri chaqirilmaydi.**"
    ),
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated, IsTeacherOrSuperAdmin])
def claim_view(request):
    ser = ClaimSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    sub = claim_submission(
        submission_id=ser.validated_data["submission_id"], teacher=request.user
    )
    return Response(TeacherSubmissionSerializer(sub).data)


@extend_schema(tags=["Teacher Checking"], summary="Grade submission and finish")
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated, IsTeacherOrSuperAdmin])
def grade_view(request):
    ser = GradeSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    sub = grade_submission(
        submission_id=ser.validated_data["submission_id"],
        teacher=request.user,
        score=ser.validated_data["score"],
        feedback=ser.validated_data.get("feedback") or "",
    )
    return Response(TeacherSubmissionSerializer(sub).data)
