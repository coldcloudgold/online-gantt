from django.forms.models import BaseModelForm
from django.urls import reverse_lazy

from gantt_chart.constants import EVENT_IDENTIFIER_FIELD, PROJECT_IDENTIFIER_FIELD
from gantt_chart.forms import DynamicChartEventLinkCreateForm
from gantt_chart.permissions import (
    EventProjectPermissionRequiredMixin,
    ProjectPermissionRequiredMixin,
    can_change_project,
    can_watch_project,
)


class ProjectParticipantMixin(ProjectPermissionRequiredMixin):
    def get_success_url(self):
        from gantt_chart.views import ProjectDetailView, ProjectListView, ProjectParticipantListView

        project = self.get_project()

        if can_change_project(self.request.user, project):
            return reverse_lazy(ProjectParticipantListView._path_name, kwargs={PROJECT_IDENTIFIER_FIELD: project.pk})
        if can_watch_project(self.request.user, project):
            return reverse_lazy(ProjectDetailView._path_name, kwargs={PROJECT_IDENTIFIER_FIELD: project.pk})

        return reverse_lazy(ProjectListView._path_name)


class EventLinkMixin(EventProjectPermissionRequiredMixin):
    def get_form_class(self) -> type[BaseModelForm]:
        project = self.get_project()
        dynamic_form = DynamicChartEventLinkCreateForm(project_pk=project.pk, label="Последователь", required=True)

        return dynamic_form.get_form()

    def get_success_url(self):
        from gantt_chart.views import EventLinkListView, ProjectListView

        project = self.get_project()

        if can_watch_project(self.request.user, project):
            return reverse_lazy(
                EventLinkListView._path_name,
                kwargs={PROJECT_IDENTIFIER_FIELD: project.pk, EVENT_IDENTIFIER_FIELD: self.get_event().pk},
            )

        return reverse_lazy(ProjectListView._path_name)
