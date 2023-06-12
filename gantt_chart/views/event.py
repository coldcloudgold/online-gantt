from typing import Any

from django.db.models.query import QuerySet
from django.forms import ValidationError
from django.forms.models import BaseModelForm
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView

from gantt_chart.constants import EVENT_IDENTIFIER_FIELD, PROJECT_IDENTIFIER_FIELD, TypeDate
from gantt_chart.forms import (
    ChartEventLinkCreateForm,
    ChartEventLinkSaveForm,
    ChartEventSaveForm,
    DynamicChartEventCreateForm,
    DynamicChartEventUpdateForm,
)
from gantt_chart.models import ChartEvent, ChartEventLink
from gantt_chart.permissions import (
    EventProjectPermissionRequiredMixin,
    ProjectPermission,
    ProjectPermissionMixin,
    ProjectPermissionRequiredMixin,
    can_watch_project,
    can_work_project,
    get_project,
    project_permission_required,
)
from gantt_chart.serializers import ChartEventActualSerializer, ChartEventPlannedSerializer, EventSerializer
from gantt_chart.service import EventService
from gantt_chart.utils import filter_queryset_event_links_by_event, filter_queryset_events_by_project

from .mixins import EventLinkMixin


class EventListView(ProjectPermissionRequiredMixin, ListView):
    """События проекта"""

    _path_name = "events"
    permission_required = can_watch_project.__name__
    model = ChartEvent
    template_name = "gantt_chart/events.html"
    paginate_by = 3000

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()

        return context

    def get_queryset(self) -> QuerySet:
        queryset = filter_queryset_events_by_project(super().get_queryset(), self.get_project()).select_related(
            "responsible"
        )

        return queryset


@project_permission_required(perms=can_work_project.__name__)
def event_create_or_update(request: HttpRequest, *args, **kwargs):
    """Создание или обновление событий проекта"""

    project_pk = kwargs[PROJECT_IDENTIFIER_FIELD]
    project = get_project(project_pk=project_pk)

    if EVENT_IDENTIFIER_FIELD in kwargs:
        event = get_object_or_404(ChartEvent, pk=kwargs[EVENT_IDENTIFIER_FIELD])
        dynamic_form = DynamicChartEventUpdateForm(project_pk, participant_label="Ответственный")
        Form = dynamic_form.get_form()  # noqa: N806
        form = Form(instance=event)
        context = {
            "title": "Редактировать событие проекта",
            "header": "Обновить событие проекта",
            "button": "Сохранить",
        }
    else:
        event = None
        dynamic_form = DynamicChartEventCreateForm(
            project_pk, event_label="Родитель", event_required=True, participant_label="Ответственный"
        )
        Form = dynamic_form.get_form()  # noqa: N806
        form = Form()
        context = {"title": "Добавить событие проекта", "header": "Создать событие проекта", "button": "Добавить"}

    if request.method == "POST":
        original_data: QueryDict = request.POST
        new_data = original_data.copy()
        new_data.update({"project": project_pk})
        save_form_data = {"data": new_data}
        if event:
            save_form_data.update({"instance": event})
            if event.parent:
                new_data.update({"parent": event.parent.pk})

        _form = ChartEventSaveForm(**save_form_data)
        try:
            _form.clean()
            _form._event_service.save(skip_validation=True)

            return redirect(EventListView._path_name, **{PROJECT_IDENTIFIER_FIELD: project_pk})

        except ValidationError:
            form._errors = _form.errors

    context.update({"form": form, "project": project})

    return render(request, "create_or_update_element.html", context=context)


event_create_or_update._path_name_create = "event_create"
event_create_or_update._path_name_update = "event_update"


class EventDeleteView(EventProjectPermissionRequiredMixin, DeleteView):
    """Удаление события проекта"""

    _path_name = "event_delete"
    permission_required = can_work_project.__name__
    model = ChartEvent
    template_name = "delete_element.html"

    def get_object(self, queryset: QuerySet) -> ChartEvent:
        obj: ChartEvent = super().get_object(queryset)
        if obj.is_root:
            raise HttpResponseBadRequest("Нельзя удалить корневое событие")

        return obj

    def form_valid(self, form: BaseModelForm) -> HttpResponseRedirect:
        return self.delete(self.request)

    def delete(self, request: HttpRequest, *args, **kwargs) -> HttpResponseRedirect:
        self.object = self.get_object()
        success_url = self.get_success_url()
        event_service = EventService(self.object)
        event_service.delete()

        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        project = self.get_project()

        return reverse_lazy(EventListView._path_name, kwargs={PROJECT_IDENTIFIER_FIELD: project.pk})


class EventLinkListView(EventProjectPermissionRequiredMixin, ListView):
    """Связи события проекта"""

    _path_name = "event_links"
    permission_required = can_watch_project.__name__
    model = ChartEventLink
    template_name = "gantt_chart/event_links.html"
    paginate_by = 3000

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_project()
        context["event"] = self.get_event()

        return context

    def get_queryset(self) -> QuerySet:
        queryset = filter_queryset_event_links_by_event(super().get_queryset(), self.get_event()).select_related(
            "follower"
        )

        return queryset


class EventLinkCreateView(EventLinkMixin, CreateView):
    """Создание связи событию проекта"""

    _path_name = "event_link_create"
    permission_required = can_work_project.__name__
    model = ChartEventLink
    form_class = ChartEventLinkCreateForm
    save_form = ChartEventLinkSaveForm
    template_name = "create_or_update_element.html"
    extra_context = {
        "title": "Добавить связь событию проекта",
        "header": "Создать связь событию проекта",
        "button": "Добавить",
    }

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        original_data: QueryDict = self.request.POST
        new_data = original_data.copy()
        event = self.get_event()
        additional_data = {"predecessor": event.pk}
        new_data.update(additional_data)
        save_form = self.save_form(new_data)

        if save_form.is_valid():
            return super().form_valid(save_form)

        form.non_field_errors = save_form.non_field_errors
        form._errors = save_form._errors

        return self.form_invalid(form)


class EventLinkUpdateView(EventLinkMixin, UpdateView):
    """Обновление связи событию проекта"""

    use_custom_identifier_field = False
    _path_name = "event_link_update"
    permission_required = can_work_project.__name__
    model = ChartEventLink
    form_class = ChartEventLinkCreateForm
    save_form = ChartEventLinkSaveForm
    template_name = "create_or_update_element.html"
    extra_context = {
        "title": "Редактировать связь событию проекта",
        "header": "Обновить связь событию проекта",
        "button": "Сохранить",
    }

    def get_form_class(self) -> type[BaseModelForm]:
        return super().get_form_class()

    def form_valid(self, form: BaseModelForm) -> HttpResponseRedirect:
        original_data: QueryDict = self.request.POST
        new_data = original_data.copy()
        additional_data = {"predecessor": form.instance.predecessor.pk}
        new_data.update(additional_data)
        save_form = self.save_form(new_data, instance=form.instance)

        try:
            save_form.save()
            return HttpResponseRedirect(self.get_success_url())

        except Exception as exception:  # noqa: F841
            form._errors = save_form.errors
            return self.form_invalid(form)


class EventLinkDeleteView(EventLinkMixin, DeleteView):
    """Удаление связи событию проекта"""

    use_custom_identifier_field = False
    _path_name = "event_link_delete"
    permission_required = can_work_project.__name__
    model = ChartEventLink
    template_name = "delete_element.html"


@project_permission_required(perms=can_watch_project.__name__)
def chart(request, *args, **kwargs):
    project_pk = kwargs[PROJECT_IDENTIFIER_FIELD]
    project = get_project(project_pk=project_pk)
    current_type_date = kwargs["type_date"]
    another_type_date = TypeDate.planned.value if current_type_date != TypeDate.planned.value else TypeDate.actual.value
    another_url = reverse_lazy(
        chart._path_name, kwargs={PROJECT_IDENTIFIER_FIELD: project_pk, "type_date": another_type_date}
    )
    context = {"project": project, "another_url": another_url}

    return render(request, "chart.html", context=context)


chart._path_name = "chart"


class ChartEventDataListAPIView(ProjectPermissionMixin, ListAPIView):
    type_date: TypeDate = None

    permission_required = can_watch_project.__name__
    permission_classes = (ProjectPermission,)
    queryset = ChartEvent.objects.all().select_related("project")

    def get_serializer_class(self):
        if self.type_date == TypeDate.planned.value:
            return ChartEventPlannedSerializer
        elif self.type_date == TypeDate.actual.value:
            return ChartEventActualSerializer

    def get_queryset(self):
        project = self.get_project()
        return super().get_queryset().filter(project=project)


def version(request, project_pk: int, type_date: str):
    def get_version_mock():
        from random import randint

        return str(randint(0, 1))

    return JsonResponse({"version": get_version_mock()}, safe=False)


class SelectEventListAPIView(ListAPIView):
    queryset = ChartEvent.objects.all().select_related("project")
    serializer_class = EventSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ("name", "hierarchical_number")
    filterset_fields = ("project",)
