from os import remove as os_remove
from os.path import isfile

from django.contrib.auth import get_user_model
from django.db.models import Model, Q, QuerySet
from django.db.models.signals import ModelSignal
from django.utils.timezone import now

from gantt_chart.models import ChartEvent, ChartEventLink, Project, ProjectParticipantRole

User = get_user_model()


def delete_file(path: str):
    """Удаление файла"""

    if isfile(path):
        os_remove(path)


def filter_queryset_project_by_user(queryset: QuerySet[Project], user: User) -> QuerySet[Project]:
    """Фильтрация доступных проектов по пользователю"""

    return queryset.filter(Q(participants_role__participant=user) | Q(is_draft=True)).distinct()


def filter_queryset_events_by_project(queryset: QuerySet[ChartEvent], project: Project) -> QuerySet[ChartEvent]:
    """Фильтрация доступных событий по проекту"""

    return queryset.filter(project=project).distinct()


def filter_queryset_event_links_by_event(queryset: QuerySet[ChartEventLink], event: ChartEvent) -> QuerySet[ChartEvent]:
    """Фильтрация доступных событий по проекту"""

    return queryset.filter(predecessor=event).distinct()


class SignalDisconnectContextManager:
    """Менеджер контекста для отключения сигнала"""

    def __init__(self, signal: ModelSignal, sender: Model, receiver: callable):
        self.signal = signal
        self.sender = sender
        self.receiver = receiver

    def __enter__(self):
        self.signal.disconnect(receiver=self.receiver, sender=self.sender)

    def __exit__(self, *args, **kwargs):
        self.signal.connect(receiver=self.receiver, sender=self.sender)


def get_or_create_root_event(project: Project) -> ChartEvent:
    root_event = ChartEvent.objects.get_root_from_project(project)
    if root_event:
        return root_event

    responsible = project.participants_role.filter(role=ProjectParticipantRole.supervisor).last()

    current_date = now().date()
    data = {
        "project": project,
        "hierarchical_number": 1,
        "name": project.name,
        "planned_start": current_date,
        "planned_end": current_date,
        "planned_duration": 1,
        "is_root": True,
    }

    if responsible:
        data["responsible"] = responsible.participant

    return ChartEvent.objects.create(**data)
