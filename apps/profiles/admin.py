# apps/profiles/admin.py
from __future__ import annotations

from decimal import Decimal

from django.contrib import admin, messages
from django.db import transaction
from django.utils.timezone import localtime

from .models import (
    StudentProfile,
    TeacherProfile,
    StudentApprovalLog,
    StudentTopUpLog,
)


class StudentApprovalLogInline(admin.TabularInline):
    model = StudentApprovalLog
    extra = 0
    can_delete = False
    fields = ("created_at", "approved", "actor", "note")
    readonly_fields = ("created_at", "approved", "actor", "note")
    ordering = ("-created_at",)
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False


class StudentTopUpLogInline(admin.TabularInline):
    model = StudentTopUpLog
    extra = 0
    can_delete = False
    fields = ("created_at", "amount", "new_balance", "actor", "note")
    readonly_fields = ("created_at", "amount", "new_balance", "actor", "note")
    ordering = ("-created_at",)
    show_change_link = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    inlines = [StudentApprovalLogInline, StudentTopUpLogInline]

    list_display = (
        "id",
        "user_fullname",
        "user_phone",
        "user_role",
        "is_approved",
        "type",
        "balance",
        "created_local",
    )
    list_filter = ("is_approved", "type", ("created_at", admin.DateFieldListFilter))
    search_fields = (
        "user__fullname",
        "user__phone_number",
        "user__telegram_username",
        "user__telegram_id",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    readonly_fields = ("created_at", "updated_at", "type")
    fieldsets = (
        ("User", {"fields": ("user",)}),
        (
            "Status",
            {"fields": ("is_approved", "type", "balance")},
        ),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user")
            .only(
                "id",
                "balance",
                "is_approved",
                "type",
                "created_at",
                "updated_at",
                "user__fullname",
                "user__phone_number",
                "user__role",
            )
        )

    @admin.display(description="User", ordering="user__fullname")
    def user_fullname(self, obj: StudentProfile) -> str:
        return obj.user.fullname

    @admin.display(description="Phone", ordering="user__phone_number")
    def user_phone(self, obj: StudentProfile) -> str:
        return obj.user.phone_number

    @admin.display(description="Role", ordering="user__role")
    def user_role(self, obj: StudentProfile) -> str:
        return obj.user.role

    @admin.display(description="Created")
    def created_local(self, obj: StudentProfile) -> str:
        return localtime(obj.created_at).strftime("%Y-%m-%d %H:%M")

    @admin.action(description="Approve selected students")
    def approve_selected(self, request, queryset):
        updated = 0
        with transaction.atomic():
            for sp in queryset.select_for_update():
                if not sp.is_approved:
                    sp.is_approved = True
                    sp.save(update_fields=["is_approved", "type", "updated_at"])
                    StudentApprovalLog.objects.create(
                        student=sp,
                        approved=True,
                        actor=request.user,
                        note="Admin approve",
                    )
                    updated += 1
        self.message_user(
            request, f"{updated} student(s) approved.", level=messages.SUCCESS
        )

    @admin.action(description="Disapprove selected students")
    def disapprove_selected(self, request, queryset):
        updated = 0
        with transaction.atomic():
            for sp in queryset.select_for_update():
                if sp.is_approved:
                    sp.is_approved = False
                    sp.save(update_fields=["is_approved", "type", "updated_at"])
                    StudentApprovalLog.objects.create(
                        student=sp,
                        approved=False,
                        actor=request.user,
                        note="Admin disapprove",
                    )
                    updated += 1
        self.message_user(
            request, f"{updated} student(s) disapproved.", level=messages.WARNING
        )

    def _bulk_topup(self, request, queryset, amount: Decimal):
        updated = 0
        with transaction.atomic():
            for sp in queryset.select_for_update():
                old = sp.balance
                new_balance = (old + amount).quantize(Decimal("0.01"))
                sp.balance = new_balance
                sp.save(update_fields=["balance", "updated_at"])
                StudentTopUpLog.objects.create(
                    student=sp,
                    amount=amount,
                    new_balance=new_balance,
                    actor=request.user,
                    note=f"Admin bulk topup +{amount}",
                )
                updated += 1
        self.message_user(
            request,
            f"Topped up {updated} student(s) by {amount} UZS.",
            level=messages.SUCCESS,
        )

    @admin.action(description="Top up +50,000 UZS")
    def topup_50k(self, request, queryset):
        self._bulk_topup(request, queryset, Decimal("50000.00"))

    @admin.action(description="Top up +100,000 UZS")
    def topup_100k(self, request, queryset):
        self._bulk_topup(request, queryset, Decimal("100000.00"))

    actions = ("approve_selected", "disapprove_selected", "topup_50k", "topup_100k")


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user_fullname", "user_phone", "created_local")
    search_fields = (
        "user__fullname",
        "user__phone_number",
        "user__telegram_username",
        "user__telegram_id",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("User", {"fields": ("user",)}),
        ("Audit", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user")
            .only(
                "id", "created_at", "updated_at", "user__fullname", "user__phone_number"
            )
        )

    @admin.display(description="User", ordering="user__fullname")
    def user_fullname(self, obj: TeacherProfile) -> str:
        return obj.user.fullname

    @admin.display(description="Phone", ordering="user__phone_number")
    def user_phone(self, obj: TeacherProfile) -> str:
        return obj.user.phone_number

    @admin.display(description="Created")
    def created_local(self, obj: TeacherProfile) -> str:
        return localtime(obj.created_at).strftime("%Y-%m-%d %H:%M")


@admin.register(StudentApprovalLog)
class StudentApprovalLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student_id",
        "approved",
        "actor_name",
        "created_local",
        "note_short",
    )
    list_filter = ("approved", ("created_at", admin.DateFieldListFilter))
    search_fields = (
        "student__user__fullname",
        "student__user__phone_number",
        "actor__fullname",
        "note",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "student",
        "approved",
        "actor",
        "note",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("student__user", "actor")
            .only(
                "id",
                "approved",
                "note",
                "created_at",
                "updated_at",
                "student__id",
                "student__user__fullname",
                "student__user__phone_number",
                "actor__fullname",
            )
        )

    @admin.display(description="Actor")
    def actor_name(self, obj: StudentApprovalLog) -> str:
        return obj.actor.fullname if obj.actor else "system"

    @admin.display(description="Created")
    def created_local(self, obj: StudentApprovalLog) -> str:
        return localtime(obj.created_at).strftime("%Y-%m-%d %H:%M")

    @admin.display(description="Note")
    def note_short(self, obj: StudentApprovalLog) -> str:
        return (obj.note or "")[:60]


@admin.register(StudentTopUpLog)
class StudentTopUpLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student_id",
        "amount",
        "new_balance",
        "actor_name",
        "created_local",
        "note_short",
    )
    list_filter = (("created_at", admin.DateFieldListFilter),)
    search_fields = (
        "student__user__fullname",
        "student__user__phone_number",
        "actor__fullname",
        "note",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "student",
        "amount",
        "new_balance",
        "actor",
        "note",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("student__user", "actor")
            .only(
                "id",
                "amount",
                "new_balance",
                "note",
                "created_at",
                "updated_at",
                "student__id",
                "student__user__fullname",
                "student__user__phone_number",
                "actor__fullname",
            )
        )

    @admin.display(description="Actor")
    def actor_name(self, obj: StudentTopUpLog) -> str:
        return obj.actor.fullname if obj.actor else "system"

    @admin.display(description="Created")
    def created_local(self, obj: StudentTopUpLog) -> str:
        return localtime(obj.created_at).strftime("%Y-%m-%d %H:%M")

    @admin.display(description="Note")
    def note_short(self, obj: StudentTopUpLog) -> str:
        return (obj.note or "")[:60]
