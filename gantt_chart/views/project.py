from typing import Any

from django.contrib.admin.options import get_content_type_for_model
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView

from gantt_chart.constants import GANTT_CHART_MODELS, PROJECT_IDENTIFIER_FIELD
from gantt_chart.forms import (
    ProjectForm,
    ProjectParticipantCreateForm,
    ProjectParticipantSaveForm,
    ProjectParticipantUpdateForm,
    UniversalCommentForm,
    UniversalCommentSaveForm,
)
from gantt_chart.models import Project, ProjectParticipant, UniversalComment, ChartEvent
from gantt_chart.permissions import (
    ProjectPermissionRequiredMixin,
    can_change_project,
    can_delete_project,
    can_watch_project,
)
from gantt_chart.serializers import ProjectParticipantSerializer
from gantt_chart.utils import SignalDisconnectContextManager, filter_queryset_project_by_user
from gantt_chart.views.mixins import ProjectParticipantMixin

User = get_user_model()


class ProjectListView(ListView):
    """Список проектов"""

    _path_name = "index"
    model = Project
    template_name = "index.html"
    extra_context = {"title": "Проекты", "header": "Проекты"}
    ordering = "name"
    paginate_by = 10

    def get_queryset(self) -> QuerySet:
        queryset = filter_queryset_project_by_user(super().get_queryset(), self.request.user)

        return queryset


class ProjectDetailView(ProjectPermissionRequiredMixin, DetailView):
    """Просмотр проекта"""

    _path_name = "project_detail"
    permission_required = can_watch_project.__name__
    model = Project
    template_name = "gantt_chart/project.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        root_event = ChartEvent.objects.get_root_from_project(obj)
        universal_comments = UniversalComment.objects.filter_with_content_type(
            content_type=self.model, object_id=obj.pk
        )
        context["object_id"] = obj.pk
        context["object_type"] = self.model.__name__
        context["root_event"] = root_event
        context["universal_comments"] = universal_comments
        form = UniversalCommentForm()
        context["form"] = form

        return context


class ProjectCreateView(CreateView):
    """Создание проекта"""

    _path_name = "project_create"
    model = Project
    form_class = ProjectForm
    template_name = "create_or_update_element.html"
    extra_context = {"title": "Добавить проект", "header": "Создать новый проект", "button": "Добавить"}

    def get_success_url(self):
        return reverse_lazy(ProjectDetailView._path_name, kwargs={PROJECT_IDENTIFIER_FIELD: self.object.pk})


class ProjectUpdateView(ProjectPermissionRequiredMixin, UpdateView):
    """Редактирование проекта"""

    _path_name = "project_update"
    permission_required = can_change_project.__name__
    model = Project
    form_class = ProjectForm
    template_name = "create_or_update_element.html"
    extra_context = {"title": "Редактировать проект", "header": "Обновить проект", "button": "Сохранить"}

    def get_success_url(self):
        return reverse_lazy(ProjectDetailView._path_name, kwargs={PROJECT_IDENTIFIER_FIELD: self.object.pk})


class ProjectDeleteView(ProjectPermissionRequiredMixin, DeleteView):
    """Удаление проекта"""

    _path_name = "project_delete"
    permission_required = can_delete_project.__name__
    model = Project
    template_name = "delete_element.html"
    success_url = reverse_lazy(ProjectListView._path_name)

    def form_valid(self, form: BaseModelForm) -> HttpResponseRedirect:
        from gantt_chart.signals import post_delete, set_actual_draft_state_from_project_participant

        success_url = self.get_success_url()
        with SignalDisconnectContextManager(
            post_delete, ProjectParticipant, set_actual_draft_state_from_project_participant
        ):
            self.object.delete()

        return HttpResponseRedirect(success_url)


class ProjectParticipantListView(ProjectPermissionRequiredMixin, ListView):
    """Список участников проекта"""

    _path_name = "project_participants"
    permission_required = can_watch_project.__name__
    model = ProjectParticipant
    template_name = "gantt_chart/project_participants.html"
    paginate_by = 1000

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        context["project"] = project

        return context

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(project=self.get_project()).select_related("participant")


class ProjectParticipantCreateView(ProjectParticipantMixin, CreateView):
    """Создание участника проекта"""

    _path_name = "project_participant_create"
    permission_required = can_change_project.__name__
    model = ProjectParticipant
    form_class = ProjectParticipantCreateForm
    save_form = ProjectParticipantSaveForm
    template_name = "create_or_update_element.html"
    extra_context = {
        "title": "Добавить участника проекта",
        "header": "Создать участника проекта",
        "button": "Добавить",
    }

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        original_data: QueryDict = self.request.POST
        new_data = original_data.copy()
        project = self.get_project()
        additional_data = {"project": project.pk}
        new_data.update(additional_data)
        save_form = self.save_form(new_data)

        if save_form.is_valid():
            return super().form_valid(save_form)

        form.non_field_errors = save_form.non_field_errors
        form._errors = save_form._errors

        return self.form_invalid(form)


class ProjectParticipantUpdateView(ProjectParticipantMixin, UpdateView):
    """Обновление роли участника проекта"""

    use_custom_identifier_field = False
    _path_name = "project_participant_update"
    permission_required = can_change_project.__name__
    model = ProjectParticipant
    form_class = ProjectParticipantUpdateForm
    save_form = ProjectParticipantSaveForm
    template_name = "create_or_update_element.html"
    extra_context = {
        "title": "Редактировать участника проекта",
        "header": "Обновить участника проекта",
        "button": "Сохранить",
    }

    def form_valid(self, form: BaseModelForm) -> HttpResponseRedirect:
        original_data: QueryDict = self.request.POST
        new_data = original_data.copy()
        project = self.get_project()
        obj = self.get_object()
        additional_data = {"project": project.pk, "participant": obj.participant.pk}
        new_data.update(additional_data)
        save_form = self.save_form(new_data, instance=form.instance)
        save_form.save()

        return HttpResponseRedirect(self.get_success_url())


class ProjectParticipantDeleteView(ProjectParticipantMixin, DeleteView):
    """Удаление участника проекта"""

    use_custom_identifier_field = False
    _path_name = "project_participant_delete"
    permission_required = can_change_project.__name__
    model = ProjectParticipant
    template_name = "delete_element.html"


@csrf_exempt
def comment_hanlde(request, object_type: str, object_id: str, pk: int | None = None):
    """
    Обработчик создания или удаления комментария, с редиректом на текущую страницу

    Логика работы:
    - При `pk` != `None` - будет попытка удалить комментарий
    - При `pk` == `None` - будет попытка создать комментарий
    """

    redirect_to = redirect(request.GET.get("next", reverse_lazy(ProjectListView._path_name)))

    if not (request.method == "POST" and object_type in GANTT_CHART_MODELS):
        return redirect_to

    content_type = get_content_type_for_model(GANTT_CHART_MODELS[object_type])
    author = request.user

    if pk:
        universal_comment = UniversalComment.objects.filter(
            pk=pk, content_type=content_type, object_id=object_id, author=author
        )
        if universal_comment.count() == 1:
            universal_comment.delete()
            return redirect_to

    original_data: QueryDict = request.POST
    new_data = original_data.copy()
    additional_data = {"content_type": content_type, "object_id": object_id, "author": author.pk}
    new_data.update(additional_data)
    form = UniversalCommentSaveForm(new_data)
    if form.is_valid():
        form.save()

    return redirect_to


class ProjectParticipantListAPIView(ListAPIView):
    queryset = ProjectParticipant.objects.all()
    serializer_class = ProjectParticipantSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ("participant__username", "participant__first_name", "participant__last_name")
    filterset_fields = ("project",)
