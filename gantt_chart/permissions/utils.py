from typing import Sequence

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission

from gantt_chart.constants import EVENT_IDENTIFIER_FIELD, PROJECT_IDENTIFIER_FIELD
from gantt_chart.models import ChartEvent, Project

from .permissions import ALL_PERMISSIONS, can_work_project

_class_project_identifier_field = f"_request_{PROJECT_IDENTIFIER_FIELD}"
_class_event_identifier_field = f"_request_{EVENT_IDENTIFIER_FIELD}"


class ProjectPermissionRequiredMixin(PermissionRequiredMixin):
    use_custom_identifier_field = True
    custom_identifier_field = PROJECT_IDENTIFIER_FIELD

    @property
    def pk_url_kwarg(self):
        return "pk" if not self.use_custom_identifier_field else self.custom_identifier_field

    def has_permission(self) -> bool:
        perms = self.get_permission_required()
        project = self.get_project()

        return _has_permission(self.request, project, perms)

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        project_identifier: int = kwargs[PROJECT_IDENTIFIER_FIELD]
        setattr(self, _class_project_identifier_field, project_identifier)

        return super().dispatch(request, *args, **kwargs)

    def get_project(self) -> Project:
        return get_project(**{PROJECT_IDENTIFIER_FIELD: getattr(self, _class_project_identifier_field)})


class EventProjectPermissionRequiredMixin(ProjectPermissionRequiredMixin):
    custom_identifier_field = EVENT_IDENTIFIER_FIELD

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        event_identifier: int = kwargs[EVENT_IDENTIFIER_FIELD]
        setattr(self, _class_event_identifier_field, event_identifier)

        return super().dispatch(request, *args, **kwargs)

    def get_event(self) -> Project:
        return get_object_or_404(ChartEvent, pk=getattr(self, _class_event_identifier_field))


def get_project(**kwargs):
    project_identifier: int = kwargs[PROJECT_IDENTIFIER_FIELD]

    return get_object_or_404(Project, pk=project_identifier)


def _has_permission(request: HttpRequest, project: Project, perms: Sequence[str]):
    for perm in perms:
        func: callable = ALL_PERMISSIONS[perm]
        if not func(request.user, project):
            return False

    return True


def project_permission_required(view_func=None, *, perms: str | Sequence[str] = (can_work_project.__name__,)):
    if view_func is None:
        return lambda view_func: project_permission_required(view_func=view_func, perms=perms)

    def _wrapper_view(request, *args, **kwargs):
        project = get_project(**kwargs)
        if not _has_permission(request, project, (perms,) if isinstance(perms, str) else perms):
            raise PermissionDenied
        res = view_func(request, *args, **kwargs)
        return res

    return _wrapper_view


class ProjectPermissionMixin:
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        project_identifier: int = kwargs[PROJECT_IDENTIFIER_FIELD]
        setattr(self, _class_project_identifier_field, project_identifier)

        return super().dispatch(request, *args, **kwargs)

    def get_project(self) -> Project:
        return get_project(**{PROJECT_IDENTIFIER_FIELD: getattr(self, _class_project_identifier_field)})


class ProjectPermission(BasePermission):
    def has_permission(self, request, view) -> bool:
        perms = getattr(view, "permission_required", ())
        if not perms:
            return True

        if isinstance(perms, str):
            perms = (perms,)

        return _has_permission(request, view.get_project(), perms)


class EventProjectPermission(ProjectPermission):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        event_identifier: int = kwargs[EVENT_IDENTIFIER_FIELD]
        setattr(self, _class_event_identifier_field, event_identifier)

        return super().dispatch(request, *args, **kwargs)
