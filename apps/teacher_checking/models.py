#  app/models/teacher_checking.py
import uuid

from django.db import models
from django.utils import timezone

from apps.user_tests.models import UserTest
from apps.users.models import User


class TeacherSubmission(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        IN_CHECKING = "in_checking", "In checking"
        CHECKED = "checked", "Checked"

    class Task(models.TextChoices):
        TASK1 = "task1", "Task 1"
        TASK2 = "task2", "Task 2"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_test = models.ForeignKey(
        UserTest, on_delete=models.CASCADE, related_name="writing_submissions"
    )
    task = models.CharField(max_length=10, choices=Task.choices)  # type: ignore[attr-defined]

    submitted_text = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.REQUESTED, db_index=True  # type: ignore[attr-defined]
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="taken_submissions",
    )

    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True, default="")

    submitted_at = models.DateTimeField(default=timezone.now)
    checked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "teacher_submissions"
        constraints = [
            models.UniqueConstraint(
                fields=["user_test", "task"], name="uniq_submission_per_task"
            ),
        ]
        indexes = [
            models.Index(fields=["status"], name="ts_status_idx"),
            models.Index(fields=["teacher", "status"], name="ts_teacher_status_idx"),
        ]

    def __str__(self):
        return f"{self.user_test_id} {self.task} {self.status}"  # type: ignore[attr-defined]
