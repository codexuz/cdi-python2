# apps/profiles/urls.py
from django.urls import path

from .views import (
    StudentMeView,
    TeacherMeView,
    StudentTopUpLogListView,
    StudentApprovalLogListView,
    student_dashboard,
    teacher_dashboard,
)

urlpatterns = [
    path("student/me/", StudentMeView.as_view(), name="student-me"),
    path("teacher/me/", TeacherMeView.as_view(), name="teacher-me"),
    path("student/topups/", StudentTopUpLogListView.as_view(), name="student-topups"),
    path(
        "student/approvals/",
        StudentApprovalLogListView.as_view(),
        name="student-approvals",
    ),
    path("student/dashboard/", student_dashboard, name="student-dashboard"),
    path("teacher/dashboard/", teacher_dashboard, name="teacher-dashboard"),
]
