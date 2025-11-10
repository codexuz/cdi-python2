#  apps/user_tests/serializers.py
from rest_framework import serializers

from apps.tests.models.ielts import Test
from .models import UserTest, TestResult


class TestListItemSerializer(serializers.ModelSerializer):
    purchased = serializers.BooleanField(read_only=True)

    class Meta:
        model = Test
        fields = ["id", "title", "created_at", "price", "purchased"]


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ["id", "title", "created_at", "price"]


class UserTestSerializer(serializers.ModelSerializer):

    test = TestSerializer(read_only=True)

    class Meta:
        model = UserTest
        fields = [
            "id",
            "test",
            "status",
            "price_paid",
            "started_at",
            "completed_at",
            "created_at",
        ]


class TestResultSerializer(serializers.ModelSerializer):

    user_test = UserTestSerializer(read_only=True)

    class Meta:
        model = TestResult
        fields = [
            "id",
            "user_test",
            "listening_score",
            "reading_score",
            "writing_score",
            "overall_score",
            "feedback",
            "errors_analysis",
            "created_at",
        ]
