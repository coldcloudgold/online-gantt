from datetime import date, timedelta
from typing import TYPE_CHECKING, Optional

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Max, Min, Sum
from django.db.models.query import QuerySet
from django.utils.timezone import now

from .mixins import ModelDiffMixin

if TYPE_CHECKING:
    from gantt_chart.models import Project

User = get_user_model()


class ChartEventManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().order_by("project", "hierarchical_number")

    def get_root_from_project(self, project: "Project") -> Optional["ChartEvent"]:
        return self.filter(project=project, is_root=True).first()


class ChartEvent(ModelDiffMixin, models.Model):
    """Событие графика"""

    project = models.ForeignKey(
        "gantt_chart.Project",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="chart_events",
        verbose_name="Проект",
    )
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children", verbose_name="Родитель"
    )
    hierarchical_number = models.CharField("Иерархический номер", max_length=2048, blank=False, null=False)
    name = models.CharField("Название", max_length=512, blank=False, null=False)
    # Даты
    planned_start = models.DateField("Планируемая дата начала", blank=False, null=False)
    planned_duration = models.PositiveIntegerField("Планируемая длительность", default=0, blank=False, null=False)
    planned_end = models.DateField("Планируемая дата окончания", blank=False, null=False)
    actual_start = models.DateField("Фактическая дата начала", blank=True, null=True)
    actual_duration = models.PositiveIntegerField("Фактическая длительность", blank=True, null=True)
    actual_end = models.DateField("Фактическая дата окончания", blank=True, null=True)
    # %
    percentage_completion = models.PositiveIntegerField(
        "Процент выполнения",
        blank=False,
        null=False,
        default=0,
        validators=(
            MinValueValidator(0, "Минимальный процент выполнения не может быть меньше 0"),
            MaxValueValidator(100, "Максимальный процент выполнения не может быть больше 100"),
        ),
    )
    is_root = models.BooleanField("Главное", default=False)
    responsible = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="event_responsible",
        verbose_name="Ответственный",
    )

    objects = ChartEventManager()

    class Meta:
        verbose_name = "Событие графика"
        verbose_name_plural = "События графика"

    def __str__(self) -> str:
        return f"{self.hierarchical_number} | {self.name}"

    def get_children(self) -> QuerySet:
        return self.__class__.objects.filter(parent=self)

    def get_min_planned_start(self) -> date:
        return self.__class__.objects.filter(project=self.project).aggregate(Min("planned_start"))["planned_start__min"]

    def get_full_planned_duration(self) -> int:
        min_planned_start = self.get_min_planned_start()
        max_planned_end = self.get_max_planned_end()
        return (max_planned_end - min_planned_start + timedelta(1)).days

    def get_rest_planned(self) -> int:
        current_date = self.get_current_date()
        max_planned_end = self.get_max_planned_end()
        return (max_planned_end - current_date - timedelta(1)).days

    def get_max_planned_end(self) -> date:
        return self.__class__.objects.filter(project=self.project).aggregate(Max("planned_end"))["planned_end__max"]

    def get_min_actual_start(self) -> Optional[date]:
        return self.__class__.objects.filter(project=self.project).aggregate(Min("actual_start"))["actual_start__min"]

    def get_max_actual_start(self) -> Optional[date]:
        return self.__class__.objects.filter(project=self.project).aggregate(Max("actual_start"))["actual_start__max"]

    def get_full_actual_duration(self) -> int:
        min_actual_start = self.get_min_actual_start()
        max_actual_start = self.get_max_actual_start()
        max_actual_end = self.get_max_actual_end()
        current_date = self.get_current_date()
        if min_actual_start:
            if max_actual_end and max_actual_end > max_actual_start:
                return (max_actual_end - min_actual_start + timedelta(1)).days
            if current_date > max_actual_start:
                return (current_date - min_actual_start + timedelta(1)).days
            return (max_actual_start - min_actual_start + timedelta(1)).days
        return 0

    def get_actual_deviation(self) -> int:
        percentage_completion = self.get_avg_percentage_completion()
        max_planned_end = self.get_max_planned_end()

        current_date = self.get_current_date()

        if percentage_completion == 0:
            return abs((max_planned_end - current_date).days) + 1

        max_actual_start = self.get_max_actual_start()
        max_actual_end = self.get_max_actual_end()
        if max_actual_end:
            max_actual_date = max_actual_start if max_actual_start > max_actual_end else max_actual_end
        else:
            max_actual_date = max_actual_start

        return abs((max_planned_end - max_actual_date).days) + 1

    def get_max_actual_end(self) -> Optional[date]:
        return self.__class__.objects.filter(project=self.project).aggregate(Max("actual_end"))["actual_end__max"]

    def get_current_date(self) -> date:
        return now().date()

    def get_avg_percentage_completion(self) -> int:
        count_events = self.__class__.objects.filter(project=self.project).count() or 1
        percentage_completion_events = self.__class__.objects.filter(project=self.project).aggregate(
            Sum("percentage_completion")
        )["percentage_completion__sum"] or 0
        return int(percentage_completion_events / count_events)

    @property
    def is_container(self) -> bool:
        return self.get_children().exists()


class ChartEventLink(models.Model):
    """Связь между событиями графика"""

    predecessor = models.ForeignKey(
        ChartEvent,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="followers_links",
        verbose_name="Предшественник",
    )
    follower = models.ForeignKey(
        ChartEvent,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="predecessors_links",
        verbose_name="Последователь",
    )

    class Meta:
        verbose_name = "Связь между событиями графика"
        verbose_name_plural = "Связи между событиями графика"
        constraints = (models.UniqueConstraint(fields=("predecessor", "follower"), name="unique_link"),)

    def __str__(self) -> str:
        return f"{self.predecessor} -> {self.follower}"
