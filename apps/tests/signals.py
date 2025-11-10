# apps/tests/signals.py
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    Test,
    Listening,
    ListeningSection,
    Reading,
    ReadingPassage,
    Writing,
    TaskOne,
    TaskTwo,
)


@receiver(post_save, sender=Test)
def create_sections_for_test(sender, instance: Test, created, **kwargs):
    if not created:
        return

    with transaction.atomic():
        listening = Listening.objects.create(title=f"{instance.title} Listening")
        sections = [
            ListeningSection(name=f"Section {i} for {instance.title}")
            for i in range(1, 5)
        ]
        ListeningSection.objects.bulk_create(sections)
        listening.sections.add(*sections)

        reading = Reading.objects.create(title=f"{instance.title} Reading")
        passages = [
            ReadingPassage(name=f"Passage {i} for {instance.title}", passage="")
            for i in range(1, 4)
        ]
        ReadingPassage.objects.bulk_create(passages)
        reading.passages.add(*passages)

        task_two = TaskTwo.objects.create(topic=f"{instance.title} Task Two")
        task_one = TaskOne.objects.create(
            topic=f"{instance.title} Task One",
            image_title="",
            image=None,
        )
        writing = Writing.objects.create(task_one=task_one, task_two=task_two)

        Test.objects.filter(pk=instance.pk).update(
            listening=listening, reading=reading, writing=writing
        )
