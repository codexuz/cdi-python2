# apps/tests/views.py
from django.db.models import Count, Prefetch
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import viewsets, mixins, permissions, filters

from apps.tests.models.ielts import Test
from apps.tests.models.listening import ListeningSection
from apps.tests.models.question import QuestionSet
from apps.tests.models.reading import ReadingPassage
from apps.tests.serializers import (
    TestListSerializer,
    TestDetailSerializer,
    QuestionSetSummarySerializer,
    QuestionSetDetailSerializer,
)

LISTENING_PREFETCH = Prefetch(
    "listening__sections",
    queryset=ListeningSection.objects.all()  # noqa
    .only("id", "name", "mp3_file")
    .prefetch_related("questions_set"),
)
READING_PREFETCH = Prefetch(
    "reading__passages",
    queryset=ReadingPassage.objects.all()  # noqa
    .only("id", "name")
    .prefetch_related("questions_set"),
)


@extend_schema(
    tags=["Tests"],
    summary="IELTS testlari ro'yxati",
    description=(
        "Barcha mavjud testlar. `ordering` parametri qo'llab-quvvatlanadi "
        "(`created_at` yoki `title`). Bo'sh bo'lsa ham `200 OK` va `[]` qaytadi."
    ),
    parameters=[
        OpenApiParameter(
            name="ordering",
            type=OpenApiTypes.STR,
            location="query",
            description="Masalan: `-created_at` yoki `title`",
        ),
    ],
    responses={
        200: OpenApiResponse(response=TestListSerializer(many=True), description="OK"),
    },
)
class TestViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        base = Test.objects.all()  # noqa
        if getattr(self, "action", None) == "list":
            return base.only("id", "title", "price", "created_at")
        return base.select_related(
            "writing__task_one", "writing__task_two", "listening", "reading"
        ).prefetch_related(LISTENING_PREFETCH, READING_PREFETCH)

    def get_serializer_class(self):
        return (
            TestListSerializer
            if getattr(self, "action", None) == "list"
            else TestDetailSerializer
        )

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=TestListSerializer(many=True), description="OK"
            ),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        responses={
            200: OpenApiResponse(response=TestDetailSerializer, description="OK"),
            404: OpenApiResponse(description="Not Found"),
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    tags=["Tests"],
    summary="Question set ro'yxati (summary)",
    description=(
        "⚠️ FRONTEND uchun emas"
        "Har bir set uchun `questions_count` qaytaradi. "
        "Bo‘sh bo‘lsa ham `200 OK` va `[]`.\n\n"
        " — bu ichki (backend / admin) API."
    ),
    responses={
        200: OpenApiResponse(
            response=QuestionSetSummarySerializer(many=True), description="OK"
        ),
    },
)
class QuestionSetViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        base = QuestionSet.objects.all()  # noqa
        if getattr(self, "action", None) == "list":
            return base.annotate(questions_count=Count("questions")).only("id", "name")
        return base.prefetch_related("questions")

    def get_serializer_class(self):
        return (
            QuestionSetSummarySerializer
            if getattr(self, "action", None) == "list"
            else QuestionSetDetailSerializer
        )

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=QuestionSetSummarySerializer(many=True), description="OK"
            ),
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=QuestionSetDetailSerializer, description="OK"
            ),
            404: OpenApiResponse(description="Not Found"),
        }
    )
    def retrieve(self, request, *args, **kwargs):

        return super().retrieve(request, *args, **kwargs)
