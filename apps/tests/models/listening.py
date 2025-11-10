#  apps/tests/models/listening.py
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .question import QuestionSet


class ListeningSection(models.Model):
    name = models.CharField(max_length=255)
    mp3_file = models.FileField(
        upload_to="listening/mp3/",
        null=True,
        blank=True,
    )
    questions_set = models.ManyToManyField(QuestionSet)

    def clean(self):
        if not self.pk:
            return
        if self.questions_set.count() > 4:
            raise ValidationError(
                f"Maximum 4 question set allowed in section {self.pk}"
            )

    class Meta:
        verbose_name = _("Listening section")
        verbose_name_plural = _("Listening sections")
        db_table = "listening_section"

    def __str__(self):
        return f"{self.name}"


class Listening(models.Model):
    title = models.CharField(default="Listening", max_length=127)
    sections = models.ManyToManyField(
        ListeningSection,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not self.pk:
            return
        if self.sections.count() > 4:
            raise ValidationError(f"Maximum 4 section allowed in listening {self.pk}")

    class Meta:
        verbose_name = _("Listening")
        verbose_name_plural = _("Listenings")
        db_table = "listening"
        ordering = ("-created_at",)
