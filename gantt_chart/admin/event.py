from typing import Any

from admin_auto_filters.filters import AutocompleteFilterFactory
from django.contrib import admin
from django.http.request import HttpRequest
from rangefilter.filters import DateRangeFilterBuilder, NumericRangeFilterBuilder

from gantt_chart.forms import ChartEventAdminForm
from gantt_chart.models import ChartEvent, ChartEventLink
from gantt_chart.service import EventService


@admin.register(ChartEvent)
class ChartEventAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "percentage_completion",
        "planned_start",
        "planned_duration",
        "planned_end",
        "actual_start",
        "actual_duration",
        "actual_end",
        "project",
        "parent",
    )
    list_display_links = ("full_name",)
    search_fields = ("name",)
    list_filter = (
        AutocompleteFilterFactory(title="Проект", base_parameter_name="project"),
        AutocompleteFilterFactory(title="Родитель", base_parameter_name="parent"),
        AutocompleteFilterFactory(title="Ответственный", base_parameter_name="responsible"),
        ("planned_start", DateRangeFilterBuilder()),
        ("planned_end", DateRangeFilterBuilder()),
        ("planned_duration", NumericRangeFilterBuilder()),
        ("actual_start", DateRangeFilterBuilder()),
        ("actual_end", DateRangeFilterBuilder()),
        ("actual_duration", NumericRangeFilterBuilder()),
        ("percentage_completion", NumericRangeFilterBuilder()),
    )
    fieldsets = (
        (None, {"fields": ("project", "parent", "hierarchical_number", "name", "is_root", "responsible")}),
        ("Плановые даты", {"fields": ("planned_start", "planned_duration", "planned_end")}),
        ("Фактические даты", {"fields": ("actual_start", "actual_duration", "actual_end")}),
        ("% выполнения", {"fields": ("percentage_completion",)}),
    )
    readonly_fields = ("is_root", "hierarchical_number", "planned_end", "actual_start", "actual_duration", "actual_end")
    autocomplete_fields = ("project", "parent", "responsible")
    form = ChartEventAdminForm

    @admin.display(description="Полное название")
    def full_name(self, obj: ChartEvent):
        return str(obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_readonly_fields(self, request: HttpRequest, obj: ChartEvent | None = None):
        default_readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            return default_readonly_fields + ("project", "parent")
        return default_readonly_fields

    def save_model(self, request: HttpRequest, obj: ChartEvent, form: Any, change: Any):
        event_service = EventService(obj)
        event_service.save(skip_validation=True)

    def delete_model(self, request: HttpRequest, obj: ChartEvent):
        event_service = EventService(obj)
        event_service.delete()
