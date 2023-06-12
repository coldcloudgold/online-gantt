from django.contrib.auth import get_user_model
from django.db.models import Q

from gantt_chart.models import Project, ProjectParticipantRole

User = get_user_model()


def can_watch_project(user: User, project: Project):
    """Право на просмотр проекта"""

    if project.is_draft:
        return True

    return project.participants_role.filter(participant=user).exists()


def can_work_project(user: User, project: Project):
    """Право на работу в проекте"""

    return project.participants_role.filter(Q(participant=user), ~Q(role=ProjectParticipantRole.observer)).exists()


def can_change_project(user: User, project: Project):
    """Право на изменение проекта"""

    if project.is_draft:
        return True

    return project.participants_role.filter(
        participant=user, role__in=(ProjectParticipantRole.supervisor, ProjectParticipantRole.administrator)
    ).exists()


def can_delete_project(user: User, project: Project):
    """Право на удаление проекта"""

    if project.is_draft:
        return True

    return project.participants_role.filter(participant=user, role=ProjectParticipantRole.supervisor).exists()


ALL_PERMISSIONS = {
    "can_watch_project": can_watch_project,
    "can_delete_project": can_delete_project,
    "can_change_project": can_change_project,
    "can_work_project": can_work_project,
}
