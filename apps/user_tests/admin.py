from django.contrib import admin
from .models import UserTest, UserAnswer, TestResult, AllTestsProxy


@admin.register(AllTestsProxy)
class AllTestsAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at")
    search_fields = ("title",)
    ordering = ("-created_at",)


@admin.register(UserTest)
class UserTestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "test", "status", "price_paid", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__fullname", "test__title")
    autocomplete_fields = ("user", "test")


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "user_test", "question", "is_correct", "created_at")
    list_filter = ("is_correct",)
    search_fields = ("user_test__user__fullname", "question__text")
    raw_id_fields = ("user_test", "question")


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_test",
        "listening_score",
        "reading_score",
        "writing_score",
        "overall_score",
        "created_at",
    )
    list_filter = ("created_at",)
    raw_id_fields = ("user_test",)
