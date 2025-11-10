# apps/speaking/serializers.py
from rest_framework import serializers
from .models import SpeakingRequest


class SpeakingRequestCreateSerializer(serializers.Serializer):
    confirm = serializers.BooleanField(required=False, default=True)


class SpeakingRequestSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source="student.id", read_only=True)

    class Meta:
        model = SpeakingRequest
        fields = [
            "id",
            "student_id",
            "status",
            "fee_amount",
            "currency",
            "note",
            "created_at",
        ]
        read_only_fields = fields
