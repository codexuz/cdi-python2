# apps/profiles/serializers.py
from rest_framework import serializers

from apps.users.models import User
from .models import StudentProfile, TeacherProfile, StudentTopUpLog, StudentApprovalLog


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "fullname",
            "telegram_username",
            "phone_number",
            "role",
            "last_activity",
        ]
        read_only_fields = fields


class StudentTopUpLogSerializer(serializers.ModelSerializer):
    actor = UserBriefSerializer(read_only=True)

    class Meta:
        model = StudentTopUpLog
        fields = ["id", "amount", "new_balance", "actor", "note", "created_at"]
        read_only_fields = fields


class StudentApprovalLogSerializer(serializers.ModelSerializer):
    actor = UserBriefSerializer(read_only=True)

    class Meta:
        model = StudentApprovalLog
        fields = ["id", "approved", "actor", "note", "created_at"]
        read_only_fields = fields


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)
    is_offline = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user",
            "balance",
            "type",
            "is_approved",
            "is_offline",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_is_offline(self, obj: StudentProfile) -> bool:  # noqa
        return obj.type == StudentProfile.TYPE_OFFLINE


class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ["id", "user", "created_at", "updated_at"]
        read_only_fields = fields


class AllTestItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    purchased = serializers.BooleanField()


class MyTestItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.CharField()
    started_at = serializers.DateTimeField(allow_null=True)
    completed_at = serializers.DateTimeField(allow_null=True)
    price_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    test = AllTestItemSerializer()  # nested min info


class ResultItemSerializer(serializers.Serializer):
    user_test_id = serializers.UUIDField()
    test_id = serializers.UUIDField()
    test_title = serializers.CharField()
    listening_score = serializers.FloatField(allow_null=True)
    reading_score = serializers.FloatField(allow_null=True)
    writing_score = serializers.FloatField(allow_null=True)
    overall_score = serializers.FloatField(allow_null=True)
    created_at = serializers.DateTimeField()


class StudentDashboardResponseSerializer(serializers.Serializer):
    profile = StudentProfileSerializer()
    sections = serializers.DictField(child=serializers.JSONField())


class SubmissionItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    user_test_id = serializers.UUIDField()
    student_fullname = serializers.CharField()
    test_title = serializers.CharField()
    task = serializers.CharField()
    status = serializers.CharField()
    score = serializers.FloatField(allow_null=True)
    submitted_at = serializers.DateTimeField()
    checked_at = serializers.DateTimeField(allow_null=True)


class TeacherDashboardResponseSerializer(serializers.Serializer):
    profile = TeacherProfileSerializer()
    sections = serializers.DictField(child=serializers.JSONField())
