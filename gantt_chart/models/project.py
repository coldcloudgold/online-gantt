from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import models
from imagekit.models import ProcessedImageField
from imagekit.processors import Resize

User = get_user_model()


class Project(models.Model):
    """Проект"""

    name = models.CharField("Название", max_length=512, unique=True, blank=False, null=False)
    description = models.TextField("Описание", blank=True)
    image = ProcessedImageField(
        verbose_name="Изображение (960x240)",
        max_length=512,
        processors=[Resize(960, 240)],
        options={"quality": 100},
        blank=True,
        null=True,
    )
    is_draft = models.BooleanField("Черновик", default=True)
    project_version = models.UUIDField(
        "Версия проекта", unique=True, blank=False, null=False, default=uuid4, editable=False
    )
    update_percentage_completion = models.BooleanField(
        "Обновлять процент выполнения родительским событиям", default=False
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"

    def __str__(self) -> str:
        return self.name


class ProjectParticipantRole(models.TextChoices):
    supervisor = "SUPERVISOR", "Руководитель"  # все права
    administrator = "ADMINISTRATOR", "Администратор"  # все права, кроме удаления
    specialist = "SPECIALIST", "Специалист"  # только редактирование графика
    observer = "OBSERVER", "Наблюдатель"  # только наблюдение


class ProjectParticipant(models.Model):
    """Участник проекта"""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="participants_role",
        verbose_name="Проект",
    )
    participant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="projects_role",
        verbose_name="Пользователь",
    )
    role = models.CharField("Роль", choices=ProjectParticipantRole.choices, max_length=64, blank=False, null=False)

    class Meta:
        verbose_name = "Роль участника проекта"
        verbose_name_plural = "Роли участников проекта"
        constraints = (
            models.UniqueConstraint(fields=("project", "participant"), name="unique_project_participant_role"),
        )

    def __str__(self) -> str:
        return self.participant.username

    def visible_role(self):
        for role in ProjectParticipantRole:
            if role == self.role:
                return role.label
