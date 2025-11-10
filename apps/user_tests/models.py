# apps/user_tests/models.py
import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from apps.tests.models.ielts import Test
from apps.tests.models.ielts import Test as RealTest
from apps.tests.models.question import Question
from apps.users.models import User


class UserTest(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_tests")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="user_tests")

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
        db_index=True,  # noqa
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    price_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_tests"
        verbose_name = "My test"
        verbose_name_plural = "My tests"
        constraints = [
            models.UniqueConstraint(fields=["user", "test"], name="uniq_user_test_once")
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="ut_user_status_idx"),
            models.Index(fields=["created_at"], name="ut_created_idx"),
        ]

    def __str__(self):
        return f"UserTest<{self.user_id}-{self.test_id}> {self.status}"

    @transaction.atomic
    def mark_started(self):
        if self.status == self.Status.NOT_STARTED:
            self.status = self.Status.IN_PROGRESS
            self.started_at = timezone.now()
            self.save(update_fields=["status", "started_at", "updated_at"])

    @transaction.atomic
    def mark_completed(self):
        if self.status != self.Status.COMPLETED:
            self.status = self.Status.COMPLETED
            self.completed_at = timezone.now()
            self.save(update_fields=["status", "completed_at", "updated_at"])


class UserAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_test = models.ForeignKey(
        UserTest, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )

    raw_answer = models.JSONField(null=True, blank=True)
    is_correct = models.BooleanField(null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "user_answers"
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        constraints = [
            models.UniqueConstraint(
                fields=["user_test", "question"], name="uniq_answer_per_question"
            )
        ]
        indexes = [
            models.Index(fields=["user_test"], name="ua_user_test_idx"),
            models.Index(fields=["question"], name="ua_question_idx"),
        ]

    def __str__(self):
        return f"UserAnswer<{self.user_test_id}-{self.question_id}> correct={self.is_correct}"


class TestResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_test = models.OneToOneField(
        UserTest, on_delete=models.CASCADE, related_name="result"
    )

    listening_score = models.FloatField(null=True, blank=True)
    reading_score = models.FloatField(null=True, blank=True)
    writing_score = models.FloatField(null=True, blank=True)
    overall_score = models.FloatField(null=True, blank=True)

    feedback = models.TextField(blank=True, default="")
    errors_analysis = models.JSONField(default=dict)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "test_results"
        verbose_name = "Result review"
        verbose_name_plural = "Result reviews"
        indexes = [
            models.Index(fields=["overall_score"], name="tr_overall_idx"),
            models.Index(fields=["created_at"], name="tr_created_idx"),
        ]

    def __str__(self):
        return f"TestResult<{self.user_test_id}> overall={self.overall_score}"


class AllTestsProxy(RealTest):
    class Meta:
        proxy = True
        app_label = "user_tests"
        verbose_name = "All test"
        verbose_name_plural = "All tests"
