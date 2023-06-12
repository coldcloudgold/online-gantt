from datetime import timedelta
from uuid import uuid4

from django.db import transaction
from django.utils.timezone import now

from gantt_chart.models import ChartEvent

from .exceptions import (
    EventRootException,
    NotValidEventException,
    ParentEventRequiredException,
    PlannedDatesException,
    PlannedEndException,
    ProjectLinkException,
    UniqueEventRootException,
)


class EventValidateService:
    """Сервис для валидации события графика"""

    __slots__ = ("_event",)

    def __init__(self, event: ChartEvent):
        self._event = event

    def validate_event_root(self, root_event: ChartEvent):
        if root_event != self._event and self._event.parent is None:
            raise UniqueEventRootException(
                f"Основное событие графика для проекта {self._event.project} уже существует - {root_event}"
            )

    def validate_event_parent(self, root_event: ChartEvent):
        if root_event != self._event:
            if self._event.parent is None:
                raise ParentEventRequiredException(f"Событие {self._event} должно иметь родителя")
            if self._event.parent == self._event:
                raise ParentEventRequiredException(f"Событие {self._event} не может ссылаться само на себя")

    def validate_project(self, root_event: ChartEvent):
        if root_event != self._event and self._event.parent.project != self._event.project:
            raise ProjectLinkException(
                f"Событие {self._event} должно быть привязано к проекту {self._event.parent.project}"
            )

    def valdate_plan_end(self):
        if self._event.planned_end is None:
            raise PlannedEndException(f"Событие {self._event} должно иметь планируемую дату окончания")

    def validate_plan_dates(self):
        if self._event.planned_start > self._event.planned_end:
            raise PlannedDatesException(
                f"Планируемая дата начала {self._event.planned_start} больше"
                f" планируемой даты окончания {self._event.planned_end}"
            )

    def validate(self):
        root_event = ChartEvent.objects.get_root_from_project(self._event.project)
        if not root_event:
            raise EventRootException(f"Основное событие графика для проекта {self._event.project} не найдено")

        self.validate_event_root(root_event)
        self.validate_event_parent(root_event)
        self.validate_project(root_event)
        self.valdate_plan_end()
        self.validate_plan_dates()


def get_event_hierarchical_number(event: ChartEvent):
    """Получение иерархического номера"""

    if not event.parent:
        return "1"

    last_childer = event.parent.get_children().last()
    if last_childer:
        hierarchical_number = int(last_childer.hierarchical_number.split(".")[-1]) + 1
    else:
        hierarchical_number = 1

    return f"{event.parent.hierarchical_number}.{hierarchical_number}"


def get_event_planned_end(event: ChartEvent):
    """Получение планируемой даты окончания"""

    return event.planned_start + timedelta(event.planned_duration - 1)


def set_event_actual_dates(event: ChartEvent):
    """Установка фактических дат для события"""

    if event.percentage_completion == 0:
        event.actual_start = None
        event.actual_duration = None
        event.actual_end = None
        return

    current_date = now().date()

    if 0 < event.percentage_completion < 100:
        if not event.actual_start:
            event.actual_start = current_date
        event.actual_duration = (current_date - event.actual_start + timedelta(1)).days
        event.actual_end = None
        return

    if event.percentage_completion == 100:
        event.actual_end = current_date
        if not event.actual_start:
            event.actual_start = current_date
        event.actual_duration = (event.actual_end - event.actual_start + timedelta(1)).days
        return


class EventService:
    """Сервис для работы с событиями графика"""

    __slots__ = ("_event", "_event_validator", "_validated_chek")

    def __init__(self, event: ChartEvent):
        self._event = event
        self._event_validator = EventValidateService(event)
        self._validated_chek = False

    def validate(self):
        """Валидация события"""

        self._set_data()
        self._event_validator.validate()
        self._validated_chek = True

    def save(self, skip_validation: bool = False):
        """Сохранение события"""

        if not skip_validation and not self._validated_chek:
            raise NotValidEventException(f"Событие {self._event} не провалидировано")

        if self._event.planned_duration == 0:
            self._event.planned_duration = 1

        with transaction.atomic():
            self._event.save()
            if self._event.project.update_percentage_completion:
                self._update_parents()
            self._update_project_version()

    def delete(self):
        """Удаление события"""

        with transaction.atomic():
            if self._event.project.update_percentage_completion:
                self._update_parents(as_deleted=True)
            self._update_project_version()
            self._event.delete()

    def _set_data(self):
        """Проставление/обновление данных для события"""

        changed_fields = self._event.changed_fields

        # Проставление hierarchical_number
        if not self._event.hierarchical_number:
            self._event.hierarchical_number = get_event_hierarchical_number(self._event)

        # Длительность не может быть 0 дней
        if self._event.planned_duration == 0:
            self._event.planned_duration = 1

        # Проставление/обновление planned_end если его нет или изменились planned_duration/planned_start
        if not self._event.planned_end or "planned_duration" in changed_fields or "planned_start" in changed_fields:
            self._event.planned_end = get_event_planned_end(self._event)

        # Обновление фактических дат
        if "percentage_completion" in changed_fields:
            set_event_actual_dates(self._event)

    def _update_parents(self, as_deleted: bool = False):  # noqa: CCR001
        """Обновление факта родителей события"""

        event_for_update = []
        current_event = self._event

        # Рекурсивно обновляем родителей
        while True:
            parent: ChartEvent = current_event.parent
            if parent is None:
                break

            # Если новый объект и percentage_completion в last_changed_fields или в changed_fields или эмуляция удаления
            if (
                as_deleted
                or current_event.newly_created
                or "percentage_completion" in current_event.last_changed_fields
                or "percentage_completion" in current_event.changed_fields
            ):
                # Забираем текущй процент выполнения
                current_event_percentage_completion = (
                    0 if as_deleted and current_event == self._event else current_event.percentage_completion
                )
                current_event_pk = current_event.pk
                # Получаем процент всех дочерних событий
                parent_all_children_percentage = (
                    sum(
                        parent.get_children()
                        .exclude(pk=current_event_pk)
                        .values_list("percentage_completion", flat=True)
                    )
                ) + current_event_percentage_completion
                # Получаем количество всех дочерних событий за исключением ребенка, от тогорого пришли
                parent_all_children_count = parent.get_children().exclude(pk=current_event_pk).count()

                # Если не эмуляция удаления или (эмуляция удаления и текущее событие не совпадает с удаялемым)
                if not as_deleted or (as_deleted and current_event != self._event):
                    parent_all_children_count += 1

                parent.percentage_completion = parent_all_children_percentage / (parent_all_children_count or 1)
                set_event_actual_dates(parent)
                event_for_update.append(parent)

            current_event = parent

        if event_for_update:
            ChartEvent.objects.bulk_update(
                event_for_update,
                (
                    "actual_start",
                    "actual_duration",
                    "actual_end",
                    "percentage_completion",
                ),
            )

    def _update_project_version(self):
        self._event.project.project_version = str(uuid4())
        self._event.project.save(update_fields=("project_version",))
