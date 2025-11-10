# apps/tests/admin.py
from django.contrib import admin
from django.db.models import Count

from .models import (
    Test,
    Listening,
    ListeningSection,
    Reading,
    ReadingPassage,
    Writing,
    TaskOne,
    TaskTwo,
    QuestionSet,
    Question,
)


class ListeningSectionInline(admin.TabularInline):
    model = Listening.sections.through
    extra = 0
    show_change_link = True


class ReadingPassageInline(admin.TabularInline):
    model = Reading.passages.through
    extra = 0
    show_change_link = True


class QuestionInline(admin.TabularInline):
    model = QuestionSet.questions.through
    extra = 0
    show_change_link = True


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("title", "price", "listening", "reading", "writing", "created_at")
    list_display_links = ("title",)
    search_fields = (
        "title",
        "listening__title",
        "reading__title",
        "writing__task_one__topic",
        "writing__task_two__topic",
    )
    list_filter = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50
    save_on_top = True
    list_select_related = ("listening", "reading", "writing")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("listening", "reading", "writing")


@admin.register(Listening)
class ListeningAdmin(admin.ModelAdmin):
    list_display = ("title", "sections_count", "created_at", "updated_at")
    search_fields = ("title", "sections__name")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = [ListeningSectionInline]
    list_per_page = 50
    save_on_top = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("sections").annotate(
            _sections_count=Count("sections")
        )

    @admin.display(description="Sections")
    def sections_count(self, obj):
        return getattr(obj, "_sections_count", 0)


@admin.register(ListeningSection)
class ListeningSectionAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "questions_count")
    search_fields = ("name", "questions_set__name", "questions_set__questions__text")
    filter_horizontal = ("questions_set",)
    ordering = ("name",)
    list_per_page = 50
    save_on_top = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_qs_count=Count("questions_set"))

    @admin.display(description="Question sets")
    def questions_count(self, obj):
        return getattr(obj, "_qs_count", 0)


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ("title", "passages_count", "created_at", "updated_at")
    search_fields = ("title", "passages__name")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = [ReadingPassageInline]
    list_per_page = 50
    save_on_top = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("passages").annotate(
            _passages_count=Count("passages")
        )

    @admin.display(description="Passages")
    def passages_count(self, obj):
        return getattr(obj, "_passages_count", 0)


@admin.register(ReadingPassage)
class ReadingPassageAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "questions_count")
    search_fields = ("name", "questions_set__name", "questions_set__questions__text")
    filter_horizontal = ("questions_set",)
    ordering = ("name",)
    list_per_page = 50
    save_on_top = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_qs_count=Count("questions_set"))

    @admin.display(description="Question sets")
    def questions_count(self, obj):
        return getattr(obj, "_qs_count", 0)


@admin.register(Writing)
class WritingAdmin(admin.ModelAdmin):
    list_display = ("id", "task_one", "task_two")
    autocomplete_fields = ("task_one", "task_two")
    list_per_page = 50
    save_on_top = True


@admin.register(TaskOne)
class TaskOneAdmin(admin.ModelAdmin):
    list_display = ("topic", "image_title")
    search_fields = ("topic", "image_title")
    ordering = ("topic",)
    list_per_page = 50
    save_on_top = True


@admin.register(TaskTwo)
class TaskTwoAdmin(admin.ModelAdmin):
    list_display = ("topic",)
    search_fields = ("topic",)
    ordering = ("topic",)
    list_per_page = 50
    save_on_top = True


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "short_text", "question_type")
    list_filter = ("question_type",)
    search_fields = ("text",)
    ordering = ("id",)
    list_per_page = 50
    save_on_top = True

    @admin.display(description="Text")
    def short_text(self, obj):
        return (obj.text[:80] + "…") if len(obj.text) > 80 else obj.text


@admin.register(QuestionSet)
class QuestionSetAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "questions_count")
    search_fields = ("name", "questions__text")
    inlines = [QuestionInline]
    ordering = ("id",)
    list_per_page = 50
    save_on_top = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_q_count=Count("questions"))

    @admin.display(description="Questions")
    def questions_count(self, obj):
        return getattr(obj, "_q_count", 0)
