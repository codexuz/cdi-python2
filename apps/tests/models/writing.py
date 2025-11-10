# apps/tests/models/writing.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class TaskTwo(models.Model):
    topic = models.CharField(max_length=255)

    def __str__(self):
        return f"WT2 {self.topic}"

    class Meta:
        verbose_name = _("Task Two")
        verbose_name_plural = _("Task Two")
        db_table = "task_two"


class TaskOne(TaskTwo):
    image_title = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to="task_one_images/", null=True, blank=True)

    def __str__(self) -> str:
        return f"WT1 {self.topic} {self.image_title}"

    class Meta:
        db_table = "task_one"
        verbose_name = _("Task One")
        verbose_name_plural = _("Task Ones")


class Writing(models.Model):
    task_one = models.ForeignKey(
        TaskOne,
        on_delete=models.CASCADE,
        related_name="writings_as_task_one",
    )
    task_two = models.ForeignKey(
        TaskTwo,
        on_delete=models.CASCADE,
        related_name="writings_as_task_two",
    )

    def __str__(self) -> str:
        return f"{self.task_one.topic} {self.task_two.topic}"
