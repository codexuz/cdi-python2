from django.contrib import admin
from .models import TeacherSubmission


@admin.register(TeacherSubmission)
class TeacherSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_test",
        "task",
        "status",
        "teacher",
        "score",
        "submitted_at",
        "checked_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "task", "teacher")
    search_fields = ("user_test__id", "teacher__username", "task")
    readonly_fields = ("created_at", "updated_at", "submitted_at", "checked_at")
