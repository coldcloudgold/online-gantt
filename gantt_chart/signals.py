from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from loguru import logger

from gantt_chart.models import Project, ProjectParticipant, ProjectParticipantRole
from gantt_chart.utils import delete_file, get_or_create_root_event


@receiver(post_delete, sender=Project)
def auto_delete_image_on_delete(sender: type[Project], instance: Project, **kwargs):
    """Удаление изображения при удалении записи"""

    try:
        if instance.image:
            path = instance.image.path
            transaction.on_commit(lambda: delete_file(path))
    except Exception:
        logger.exception("Ошибка при удалении изображения")


@receiver(pre_save, sender=Project)
def auto_delete_image_on_change(sender: type[Project], instance: Project, **kwargs):
    """Удаление изображения при замене на новое изображение"""

    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
        if not old_instance.image:
            return

        old_path = old_instance.image.path

        new_path = instance.image.path

        if old_path != new_path:
            delete_file(old_path)

    except sender.DoesNotExist:
        return

    except Exception:
        logger.exception("Ошибка при удалении изображения")


@receiver(pre_save, sender=Project)
def set_actual_draft_state_from_project(sender: type[Project], instance: Project, **kwargs):
    """
    Установка статуса черновика проекта

    Если нет назначенных людей в проекте с ролью "Руководитель" или "Администратор" - проект имеет статус черновика
    """

    logger.debug(f"set_actual_draft_state_from_project | 1. {instance.is_draft=}")
    if not instance.pk:
        instance.is_draft = True
        logger.debug(f"set_actual_draft_state_from_project | 2. {instance.is_draft=}")
        return

    if not instance.participants_role.filter(
        Q(role=ProjectParticipantRole.supervisor) | Q(role=ProjectParticipantRole.administrator)
    ).exists():
        instance.is_draft = True
        logger.debug(f"set_actual_draft_state_from_project | 3. {instance.is_draft=}")
    else:
        instance.is_draft = False
        logger.debug(f"set_actual_draft_state_from_project | 4. {instance.is_draft=}")
    logger.debug(f"set_actual_draft_state_from_project | 5. {instance.is_draft=}")


@receiver(post_save, sender=Project)
def create_root_event(sender: type[Project], instance: Project, **kwargs):
    """Создание корневого события проекта"""
    get_or_create_root_event(instance)


@receiver((post_save, post_delete), sender=ProjectParticipant)
def set_actual_draft_state_from_project_participant(
    sender: type[ProjectParticipant], instance: ProjectParticipant, **kwargs
):
    """
    Установка статуса черновика проекта

    Если нет назначенных людей в проекте с ролью "Руководитель" или "Администратор" - проект имеет статус черновика
    """

    logger.debug(f"set_actual_draft_state_from_project_participant | 1. {instance.project.is_draft=}")
    with transaction.atomic():
        transaction.on_commit(lambda: instance.project.save())
    logger.debug(f"set_actual_draft_state_from_project_participant | 2. {instance.project.is_draft=}")
