#  app/apps/tests/serializers/__init__.py
from rest_framework import serializers
from apps.tests.models.ielts import Test
from apps.tests.models.listening import Listening, ListeningSection
from apps.tests.models.reading import Reading, ReadingPassage
from apps.tests.models.writing import Writing, TaskOne, TaskTwo
from apps.tests.models.question import Question, QuestionSet


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            "text",
            "options",
            "table",
            "answer_dict",
            "answer_list",
        ]


class QuestionSetSummarySerializer(serializers.ModelSerializer):
    questions_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = QuestionSet
        fields = ["id", "name", "questions_count"]


class QuestionSetDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionSet
        fields = ["id", "name", "questions"]


class ListeningSectionSummarySerializer(serializers.ModelSerializer):
    question_set_ids = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source="questions_set"
    )

    class Meta:
        model = ListeningSection
        fields = ["id", "name", "mp3_file", "question_set_ids"]


class ListeningDetailSerializer(serializers.ModelSerializer):
    sections = ListeningSectionSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Listening
        fields = ["id", "title", "sections"]


class ReadingPassageSummarySerializer(serializers.ModelSerializer):
    question_set_ids = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source="questions_set"
    )

    class Meta:
        model = ReadingPassage
        fields = ["id", "name", "question_set_ids"]


class ReadingDetailSerializer(serializers.ModelSerializer):
    passages = ReadingPassageSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Reading
        fields = ["id", "title", "passages"]


class TaskOneSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskOne
        fields = ["id", "topic", "image_title", "image"]


class TaskTwoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTwo
        fields = ["id", "topic"]


class WritingDetailSerializer(serializers.ModelSerializer):
    task_one = TaskOneSerializer(read_only=True)
    task_two = TaskTwoSerializer(read_only=True)

    class Meta:
        model = Writing
        fields = ["id", "task_one", "task_two"]


class TestListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ["id", "title", "price", "created_at"]


class TestDetailSerializer(serializers.ModelSerializer):
    listening = ListeningDetailSerializer(read_only=True)
    reading = ReadingDetailSerializer(read_only=True)
    writing = WritingDetailSerializer(read_only=True)

    class Meta:
        model = Test
        fields = [
            "id",
            "title",
            "price",
            "listening",
            "reading",
            "writing",
            "created_at",
            "updated_at",
        ]
