# apps/profiles/signals.py
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import User
from .models import StudentProfile, TeacherProfile


@receiver(post_save, sender=User)
def create_role_profile(sender, instance: User, created: bool, **kwargs):
    if not created:
        return
    with transaction.atomic():
        if instance.role == User.Roles.STUDENT:
            StudentProfile.objects.get_or_create(user=instance)
        elif instance.role == User.Roles.TEACHER:
            TeacherProfile.objects.get_or_create(user=instance)
