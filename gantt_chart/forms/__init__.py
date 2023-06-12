from typing import Any

from bootstrap_datepicker_plus.widgets import DatePickerInput
from django.contrib.auth import get_user_model
from django.forms import ModelForm, ValidationError
from django_select2 import forms as s2forms

from gantt_chart.models import ChartEvent, ChartEventLink, Project, ProjectParticipant, UniversalComment
from gantt_chart.service import EventService

from .dynamic import make_dynamic_event_select2_field, make_dynamic_participant_select2_field

User = get_user_model()


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "image", "update_percentage_completion")


class UserWidget(s2forms.ModelSelect2Widget):
    search_fields = ("username__icontains", "first_name__icontains", "last_name__icontains")


class ProjectParticipantCreateForm(ModelForm):
    class Meta:
        model = ProjectParticipant
        fields = ("participant", "role")
        widgets = {"participant": UserWidget}


class ProjectParticipantUpdateForm(ModelForm):
    class Meta:
        model = ProjectParticipant
        fields = ("role",)


class ProjectParticipantSaveForm(ModelForm):
    class Meta:
        model = ProjectParticipant
        fields = "__all__"


class UniversalCommentForm(ModelForm):
    class Meta:
        model = UniversalComment
        fields = ("comment",)


class UniversalCommentSaveForm(ModelForm):
    class Meta:
        model = UniversalComment
        fields = "__all__"


class ChartEventValidationMixin:
    def clean(self) -> dict[str, Any]:
        # Стандартная валидация на заполненность обязательных полей
        is_valid = super().is_valid()
        if not is_valid:
            raise ValidationError("Ошибка валидации")

        # Установка атрибутов обязательных полей инстансу
        for field, value in self.cleaned_data.items():
            setattr(self.instance, field, value)

        # Перехват и рейз ошибки сервиса в админку
        self._event_service = EventService(self.instance)
        self._event_service.validate()
        try:
            self._event_service.validate()
        except Exception as exception:
            raise ValidationError(exception)

        return super().clean()


class ChartEventAdminForm(ChartEventValidationMixin, ModelForm):
    class Meta:
        model = ChartEvent
        fields = "__all__"


class ChartEventSaveForm(ChartEventValidationMixin, ModelForm):
    class Meta:
        model = ChartEvent
        exclude = ("is_root", "hierarchical_number", "planned_end")


class ChartEventCreateForm(ChartEventValidationMixin, ModelForm):
    class Meta:
        model = ChartEvent
        fields = "__all__"
        exclude = (
            "project",
            "is_root",
            "hierarchical_number",
            "planned_end",
            "actual_start",
            "actual_duration",
            "actual_end",
        )
        widgets = {"planned_start": DatePickerInput}


class DynamicChartEventCreateForm:
    def __init__(
        self,
        project_pk: int,
        event_label: str = None,
        event_required: bool = False,
        participant_label: str = None,
        participant_required: bool = False,
    ) -> None:
        self.parent = make_dynamic_event_select2_field(project_pk, event_label, event_required)
        self.responsible = make_dynamic_participant_select2_field(project_pk, participant_label, participant_required)

    def get_form(self):
        class _ChartEventCreateForm(ChartEventCreateForm):
            parent = self.parent
            responsible = self.responsible

        return _ChartEventCreateForm


class ChartEventUpdateForm(ChartEventCreateForm):
    class Meta(ChartEventCreateForm.Meta):
        exclude = ChartEventCreateForm.Meta.exclude + ("parent",)


class DynamicChartEventUpdateForm:
    def __init__(
        self,
        project_pk: int,
        participant_label: str = None,
        participant_required: bool = False,
    ) -> None:
        self.responsible = make_dynamic_participant_select2_field(project_pk, participant_label, participant_required)

    def get_form(self):
        class _ChartEventUpdateForm(ChartEventUpdateForm):
            responsible = self.responsible

        return _ChartEventUpdateForm


class ChartEventLinkCreateForm(ModelForm):
    class Meta:
        model = ChartEventLink
        fields = ("follower",)


class DynamicChartEventLinkCreateForm(ModelForm):
    def __init__(self, project_pk: int, label: str = None, required: bool = False):
        self.follower = make_dynamic_event_select2_field(project_pk, label, required)

    def get_form(self):
        class _ChartEventLinkCreateForm(ChartEventLinkCreateForm):
            follower = self.follower

        return _ChartEventLinkCreateForm


class ChartEventLinkSaveForm(ModelForm):
    class Meta:
        model = ChartEventLink
        fields = "__all__"
