#  apps/teacher_checking/serializers.py
from rest_framework import serializers
from apps.users.serializers import UserReadSerializer
from apps.user_tests.serializers import UserTestSerializer
from .models import TeacherSubmission


class TeacherSubmissionSerializer(serializers.ModelSerializer):
    user_test = UserTestSerializer(read_only=True)
    teacher = UserReadSerializer(read_only=True)

    class Meta:
        model = TeacherSubmission
        fields = [
            "id",
            "user_test",
            "task",
            "submitted_text",
            "status",
            "teacher",
            "score",
            "feedback",
            "submitted_at",
            "checked_at",
        ]
        read_only_fields = [
            "status",
            "teacher",
            "score",
            "feedback",
            "submitted_at",
            "checked_at",
        ]


class SubmissionCreateSerializer(serializers.Serializer):
    user_test_id = serializers.UUIDField()
    task = serializers.ChoiceField(choices=TeacherSubmission.Task.choices)  # type: ignore[attr-defined]
    text = serializers.CharField()


class ClaimSerializer(serializers.Serializer):
    submission_id = serializers.UUIDField()


class GradeSerializer(serializers.Serializer):
    submission_id = serializers.UUIDField()
    score = serializers.FloatField(min_value=0, max_value=9)
    feedback = serializers.CharField(allow_blank=True, required=False)
