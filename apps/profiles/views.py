#  apps/profiles/views.py
from __future__ import annotations

from typing import Dict, Any, List

from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.teacher_checking.models import TeacherSubmission
from apps.tests.models.ielts import Test
from apps.user_tests.models import UserTest, TestResult
from .models import (
    StudentProfile,
    TeacherProfile,
    StudentTopUpLog,
    StudentApprovalLog,
)
from .permissions import IsStudent, IsTeacherOrSuperAdmin
from .serializers import (
    StudentProfileSerializer,
    TeacherProfileSerializer,
    StudentTopUpLogSerializer,
    StudentApprovalLogSerializer,
    AllTestItemSerializer,
    MyTestItemSerializer,
    ResultItemSerializer,
    StudentDashboardResponseSerializer,
    TeacherDashboardResponseSerializer,
)


def _qp_int(qp, key: str, default: int = 0) -> int:
    try:
        return int(qp.get(key, default))
    except (TypeError, ValueError):
        return default


def _sub_to_item(s: TeacherSubmission) -> Dict[str, Any]:

    ut = s.user_test
    return {
        "id": s.id,
        "user_test_id": s.user_test_id,  # type: ignore[attr-defined]
        "student_fullname": ut.user.fullname,
        "test_title": ut.test.title,
        "task": s.task,
        "status": s.status,
        "score": s.score,
        "submitted_at": s.submitted_at,
        "checked_at": s.checked_at,
    }


@extend_schema(tags=["Profiles"], summary="Student profil (meniki)")
class StudentMeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    serializer_class = StudentProfileSerializer

    def get_object(self) -> StudentProfile:
        return get_object_or_404(  # noqa
            StudentProfile.objects.select_related("user"),
            user=self.request.user,
        )


@extend_schema(tags=["Profiles"], summary="Teacher profil (meniki)")
class TeacherMeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsTeacherOrSuperAdmin]
    serializer_class = TeacherProfileSerializer

    def get_object(self) -> TeacherProfile:
        return get_object_or_404(  # noqa
            TeacherProfile.objects.select_related("user"),
            user=self.request.user,
        )


@extend_schema(
    tags=["Profiles"],
    summary="Student top-up loglari",
    parameters=[
        OpenApiParameter(
            name="limit",
            type=OpenApiTypes.INT,
            location="query",
            description="Qatorlar soni (ixtiyoriy).",
        )
    ],
)
class StudentTopUpLogListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    serializer_class = StudentTopUpLogSerializer

    def get_queryset(self):
        sp = get_object_or_404(StudentProfile, user=self.request.user)
        qs = (
            StudentTopUpLog.objects.filter(student=sp)
            .select_related("actor")
            .order_by("-created_at")
        )
        limit = _qp_int(self.request.query_params, "limit")  # type: ignore[attr-defined]
        return qs[:limit] if limit > 0 else qs


@extend_schema(
    tags=["Profiles"],
    summary="Student approval loglari",
    description=(
        "⚠️ **FRONTEND uchun emas!**\n\n"
        "Ushbu endpoint faqat **admin yoki backend tizim** tomonidan "
        "studentning tasdiqlanish tarixini (approval loglarini) ko‘rish uchun ishlatiladi."
    ),
)
class StudentApprovalLogListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    serializer_class = StudentApprovalLogSerializer

    def get_queryset(self):
        sp = get_object_or_404(StudentProfile, user=self.request.user)
        return (
            StudentApprovalLog.objects.filter(student=sp)
            .select_related("actor")
            .order_by("-created_at")
        )


@extend_schema(
    tags=["Profiles"],
    summary="Student dashboard: profile + all_tests + my_tests + results",
    parameters=[
        OpenApiParameter(
            name="all_limit",
            type=OpenApiTypes.INT,
            location="query",
            description="All tests limit.",
        ),
        OpenApiParameter(
            name="my_limit",
            type=OpenApiTypes.INT,
            location="query",
            description="My tests limit.",
        ),
        OpenApiParameter(
            name="res_limit",
            type=OpenApiTypes.INT,
            location="query",
            description="Results limit.",
        ),
    ],
    responses={200: StudentDashboardResponseSerializer},
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsStudent])
def student_dashboard(request):

    user = request.user
    sp = get_object_or_404(  # noqa
        StudentProfile.objects.select_related("user"),
        user=user,
    )

    all_limit = _qp_int(request.query_params, "all_limit")
    my_limit = _qp_int(request.query_params, "my_limit")
    res_limit = _qp_int(request.query_params, "res_limit")

    purchased_qs = UserTest.objects.filter(user=user, test=OuterRef("pk"))
    all_qs = (
        Test.objects.all()
        .annotate(purchased=Exists(purchased_qs))
        .order_by("-created_at")
    )
    if all_limit > 0:
        all_qs = all_qs[:all_limit]

    all_tests: List[Dict[str, Any]] = [
        {
            "id": t.id,  # type: ignore[attr-defined]
            "title": t.title,
            "price": getattr(t, "price", 0),
            "purchased": bool(getattr(t, "purchased", False)),
        }
        for t in all_qs
    ]
    all_tests_data = AllTestItemSerializer(all_tests, many=True).data

    my_qs = (
        UserTest.objects.filter(user=user)
        .select_related("test")
        .order_by("-created_at")
    )
    if my_limit > 0:
        my_qs = my_qs[:my_limit]

    my_tests: List[Dict[str, Any]] = [
        {
            "id": ut.id,
            "status": ut.status,
            "started_at": ut.started_at,
            "completed_at": ut.completed_at,
            "price_paid": ut.price_paid,
            "test": {
                "id": ut.test.id,
                "title": ut.test.title,
                "price": getattr(ut.test, "price", 0),
                "purchased": True,
            },
        }
        for ut in my_qs
    ]
    my_tests_data = MyTestItemSerializer(my_tests, many=True).data

    res_qs = (
        TestResult.objects.filter(user_test__user=user)
        .select_related("user_test__test")
        .order_by("-created_at")
    )
    if res_limit > 0:
        res_qs = res_qs[:res_limit]

    results: List[Dict[str, Any]] = [
        {
            "user_test_id": tr.user_test_id,  # type: ignore[attr-defined]
            "test_id": tr.user_test.test_id,
            "test_title": tr.user_test.test.title,
            "listening_score": tr.listening_score,
            "reading_score": tr.reading_score,
            "writing_score": tr.writing_score,
            "overall_score": tr.overall_score,
            "created_at": tr.created_at,
        }
        for tr in res_qs
    ]
    results_data = ResultItemSerializer(results, many=True).data

    return Response(
        {
            "profile": StudentProfileSerializer(sp).data,
            "sections": {
                "all_tests": all_tests_data,
                "my_tests": my_tests_data,
                "results": results_data,
            },
        }
    )


@extend_schema(
    tags=["Profiles"],
    summary="Teacher dashboard: profile + all_writing + my_checking + my_checked",
    parameters=[
        OpenApiParameter(
            name="all_limit",
            type=OpenApiTypes.INT,
            location="query",
            description="All writing limit.",
        ),
        OpenApiParameter(
            name="chk_limit",
            type=OpenApiTypes.INT,
            location="query",
            description="My checking limit.",
        ),
        OpenApiParameter(
            name="done_limit",
            type=OpenApiTypes.INT,
            location="query",
            description="My checked limit.",
        ),
    ],
    responses={200: TeacherDashboardResponseSerializer},
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsTeacherOrSuperAdmin])
def teacher_dashboard(request):

    user = request.user
    tp = get_object_or_404(  # type: ignore[var-annotated]
        TeacherProfile.objects.select_related("user"),
        user=user,
    )

    all_limit = _qp_int(request.query_params, "all_limit")
    chk_limit = _qp_int(request.query_params, "chk_limit")
    done_limit = _qp_int(request.query_params, "done_limit")

    base_sel = ("user_test__user", "user_test__test", "teacher")

    all_qs = (
        TeacherSubmission.objects.filter(status=TeacherSubmission.Status.REQUESTED)
        .select_related(*base_sel)
        .order_by("submitted_at")
    )
    all_count = all_qs.count()
    if all_limit > 0:
        all_qs = all_qs[:all_limit]

    chk_qs = (
        TeacherSubmission.objects.filter(
            status=TeacherSubmission.Status.IN_CHECKING, teacher=user
        )
        .select_related(*base_sel)
        .order_by("-updated_at")
    )
    chk_count = chk_qs.count()
    if chk_limit > 0:
        chk_qs = chk_qs[:chk_limit]

    done_qs = (
        TeacherSubmission.objects.filter(
            status=TeacherSubmission.Status.CHECKED, teacher=user
        )
        .select_related(*base_sel)
        .order_by("-checked_at")
    )
    done_count = done_qs.count()
    if done_limit > 0:
        done_qs = done_qs[:done_limit]

    return Response(
        {
            "profile": TeacherProfileSerializer(tp).data,
            "sections": {
                "all_writing": {
                    "count": all_count,
                    "items": [_sub_to_item(x) for x in all_qs],
                },
                "my_checking": {
                    "count": chk_count,
                    "items": [_sub_to_item(x) for x in chk_qs],
                },
                "my_checked": {
                    "count": done_count,
                    "items": [_sub_to_item(x) for x in done_qs],
                },
            },
        }
    )
