#  apps/tests/models/question.py
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import JSONField


class QuestionType(models.TextChoices):
    R_YES_NO_NOT_GIVEN = "R_YES_NO_NOT_GIVEN", _("Reading: Yes/No/Not Given")
    R_TRUE_FALSE_NOT_GIVEN = "R_TRUE_FALSE_NOT_GIVEN", _(
        "Reading: True/False/Not Given"
    )
    R_MULTIPLE_CHOICE = "R_MULTIPLE_CHOICE", _("Reading: Multiple Choice")
    R_MATCHING_INFORMATION = "R_MATCHING_INFORMATION", _(
        "Reading: Matching Information"
    )
    R_MATCHING_HEADINGS = "R_MATCHING_HEADINGS", _("Reading: Matching Headings")
    R_MATCHING_FEATURES = "R_MATCHING_FEATURES", _("Reading: Matching Features")
    R_MATCHING_SENTENCE_ENDINGS = "R_MATCHING_SENTENCE_ENDINGS", _(
        "Reading: Matching Sentence Endings"
    )
    R_SENTENCE_COMPLETION = "R_SENTENCE_COMPLETION", _("Reading: Sentence Completion")
    R_SUMMARY_COMPLETION = "R_SUMMARY_COMPLETION", _("Reading: Summary Completion")
    R_SHORT_ANSWER = "R_SHORT_ANSWER", _("Reading: Short Answer")
    R_DIAGRAM_COMPLETION = "R_DIAGRAM_COMPLETION", _("Reading: Diagram Completion")

    L_MULTIPLE_CHOICE = "L_MULTIPLE_CHOICE", _("Listening: Multiple Choice")
    L_MATCHING_HEADINGS = "L_MATCHING_HEADINGS", _("Listening: Matching Headings")
    L_DIAGRAM_LABELLING = "L_DIAGRAM_LABELLING", _("Listening: Diagram Labelling")
    L_FORM_COMPLETION = "L_FORM_COMPLETION", _("Listening: Form Completion")
    L_SENTENCE_COMPLETION = "L_SENTENCE_COMPLETION", _("Listening: Sentence Completion")
    L_SHORT_ANSWER = "L_SHORT_ANSWER", _("Listening: Short Answer")


def is_reading_type(t: str) -> bool:
    return t.startswith("R_")


def is_listening_type(t: str) -> bool:
    return t.startswith("L_")


class Question(models.Model):
    text = models.TextField(help_text=_("Main question text shown to the student."))
    question_type = models.CharField(
        max_length=50,
        choices=QuestionType.choices,  # type: ignore[attr-defined]
        default=QuestionType.R_YES_NO_NOT_GIVEN,
        help_text=_("Select the type (prefixed with R_ or L_)."),
    )
    options = JSONField(
        default=list,
        help_text=_("List of option objects (if applicable)."),
        null=True,
        blank=True,
    )

    table = JSONField(
        default=dict, help_text=_("Table of question data."), null=True, blank=True
    )
    answer_dict = JSONField(
        default=dict, help_text=_("Answer key data."), null=True, blank=True
    )
    answer_list = JSONField(
        default=list, help_text=_("Answer key data."), null=True, blank=True
    )

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        db_table = "questions"

    def __str__(self):
        return f"{self.question_type}: {self.text[:48]}"


class QuestionSet(models.Model):
    name = models.CharField(
        max_length=127,
        help_text=_("Name of the question set (e.g., 'Reading Passage 1 MCQ')."),
    )
    questions = models.ManyToManyField(
        Question,
        related_name="sets",
        help_text=_("Questions included in this set (aim for 10–15)."),
    )

    class Meta:
        verbose_name = _("Question set")
        verbose_name_plural = _("Question sets")

    def __str__(self):
        return f"{self.name} {self.questions.first().question_type}"

    @staticmethod
    def _validate_uniform_question_type_from_types(type_values: set):
        if not type_values:
            raise ValidationError(_("Question set cannot be empty."))
        if len(type_values) != 1:
            raise ValidationError(
                _("All questions in a set must share the same question_type.")
            )

    def validate_uniform_question_type(self):
        types = set(self.questions.values_list("question_type", flat=True))
        self._validate_uniform_question_type_from_types(types)

    def clean(self):
        super().clean()
        if self.pk:
            self.validate_uniform_question_type()
