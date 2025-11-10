#  apps/tests/models/reading.py
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .question import QuestionSet


class ReadingPassage(models.Model):
    name = models.CharField(max_length=255)
    passage = models.TextField()
    questions_set = models.ManyToManyField(QuestionSet)

    def clean(self):
        if not self.pk:
            return
        if self.questions_set.count() > 3:
            raise ValidationError(
                f"Maximum 3 question sets allowed in passage {self.pk}"
            )

    class Meta:
        verbose_name = _("Reading passage")
        verbose_name_plural = _("Reading passages")
        db_table = "reading_passage"

    def __str__(self):
        return self.name


class Reading(models.Model):
    title = models.CharField(default="Reading", max_length=127)
    passages = models.ManyToManyField(ReadingPassage)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not self.pk:
            return
        if self.passages.count() > 3:
            raise ValidationError(f"Maximum 3 passages allowed in reading {self.pk}")

    class Meta:
        verbose_name = _("Reading")
        verbose_name_plural = _("Readings")
        db_table = "reading"
        ordering = ("-created_at",)

    def __str__(self):
        return self.title
