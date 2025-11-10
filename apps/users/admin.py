# apps/users/admin.py
from __future__ import annotations

import re
from typing import Optional

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import User

StudentInline = None
TeacherInline = None
try:
    from apps.profiles.models import StudentProfile, TeacherProfile

    class StudentInline(admin.StackedInline):
        model = StudentProfile
        can_delete = False
        extra = 0
        fields = ("balance", "is_approved", "type", "created_at", "updated_at")
        readonly_fields = ("type", "created_at", "updated_at")

    class TeacherInline(admin.StackedInline):
        model = TeacherProfile
        can_delete = False
        extra = 0
        fields = ("created_at", "updated_at")
        readonly_fields = ("created_at", "updated_at")

except Exception:
    pass


_phone_re = re.compile(r"^\+?[1-9]\d{7,14}$")
_tg_username_re = re.compile(r"^[A-Za-z0-9_]{5,32}$")


def _normalize_tg_username(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    v = v.strip().lstrip("@").lower()
    if not _tg_username_re.match(v):
        raise forms.ValidationError(
            "Invalid Telegram username (5–32 chars, A-z/0-9/_)."
        )
    return v


def _validate_phone(v: str) -> str:
    v = (v or "").strip().replace(" ", "").replace("-", "")
    if not _phone_re.match(v):
        raise forms.ValidationError("Phone must be E.164-like, e.g. +998901234567")
    return v


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password", widget=forms.PasswordInput, required=False
    )
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput, required=False
    )

    class Meta:
        model = User
        fields = (
            "fullname",
            "phone_number",
            "role",
            "telegram_username",
            "is_staff",
            "is_active",
        )

    def clean_phone_number(self):
        return _validate_phone(self.cleaned_data.get("phone_number"))

    def clean_telegram_username(self):
        v = self.cleaned_data.get("telegram_username")
        return _normalize_tg_username(v)

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Passwords don't match.")
        return cleaned

    def save(self, commit=True):
        user: User = super().save(commit=False)
        # normalize tg username again (server-side safety)
        user.telegram_username = _normalize_tg_username(
            self.cleaned_data.get("telegram_username")
        )
        # set password (or unusable)
        p1 = self.cleaned_data.get("password1")
        if p1:
            user.set_password(p1)
        else:
            user.set_unusable_password()
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label="Password", help_text="Raw passwords are not stored."
    )

    class Meta:
        model = User
        fields = (
            "fullname",
            "phone_number",
            "role",
            "telegram_id",
            "telegram_username",
            "password",
            "is_staff",
            "is_active",
            "is_superuser",
            "groups",
            "user_permissions",
        )

    def clean_phone_number(self):
        return _validate_phone(self.cleaned_data.get("phone_number"))

    def clean_telegram_username(self):
        v = self.cleaned_data.get("telegram_username")
        return _normalize_tg_username(v)

    def save(self, commit=True):
        user: User = super().save(commit=False)
        user.telegram_username = _normalize_tg_username(
            self.cleaned_data.get("telegram_username")
        )
        if commit:
            user.save()
        return user


# ============================
# Admin
# ============================
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User

    list_display = (
        "fullname",
        "phone_number",
        "role",
        "telegram_id",
        "telegram_username",
        "is_staff",
        "is_active",
        "created_at",
        "last_activity",
    )
    list_display_links = ("fullname", "phone_number")
    list_filter = ("role", "is_staff", "is_active", "created_at")
    search_fields = ("fullname", "phone_number", "telegram_username", "telegram_id")
    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at", "last_activity")

    fieldsets = (
        ("Identity", {"fields": ("fullname", "phone_number", "role")}),
        (
            "Telegram",
            {"fields": ("telegram_id", "telegram_username")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at", "last_activity")},
        ),
        ("Password", {"fields": ("password",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "fullname",
                    "phone_number",
                    "role",
                    "telegram_username",
                    "is_staff",
                    "is_active",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    if StudentInline:
        inlines = [StudentInline]
        if TeacherInline:
            inlines.append(TeacherInline)

    @admin.action(description="Mark as active")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) marked active.")

    @admin.action(description="Mark as inactive")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) marked inactive.")

    actions = ("make_active", "make_inactive")
