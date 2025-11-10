# apps/tests/signals_m2m.py
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .models.listening import Listening, ListeningSection
from .models.reading import Reading, ReadingPassage


@receiver(m2m_changed, sender=Listening.sections.through)
def limit_listening_sections(sender, instance: Listening, action, pk_set, **kwargs):
    if action == "pre_add":
        incoming = len(pk_set or [])
        if instance.sections.count() + incoming > 4:
            raise ValidationError(
                "Listening ichida maksimal 4 ta section bo‘lishi mumkin."
            )


@receiver(m2m_changed, sender=ListeningSection.questions_set.through)
def limit_section_question_sets(
    sender, instance: ListeningSection, action, pk_set, **kwargs
):
    if action == "pre_add":
        incoming = len(pk_set or [])
        if instance.questions_set.count() + incoming > 4:
            raise ValidationError(
                "Section ichida maksimal 4 ta question set bo‘lishi mumkin."
            )


@receiver(m2m_changed, sender=Reading.passages.through)
def limit_reading_passages(sender, instance: Reading, action, pk_set, **kwargs):
    if action == "pre_add":
        incoming = len(pk_set or [])
        if instance.passages.count() + incoming > 3:
            raise ValidationError(
                "Reading ichida maksimal 3 ta passage bo‘lishi mumkin."
            )


@receiver(m2m_changed, sender=ReadingPassage.questions_set.through)
def limit_passage_question_sets(
    sender, instance: ReadingPassage, action, pk_set, **kwargs
):
    if action == "pre_add":
        incoming = len(pk_set or [])
        if instance.questions_set.count() + incoming > 3:
            raise ValidationError(
                "Passage ichida maksimal 3 ta question set bo‘lishi mumkin."
            )
