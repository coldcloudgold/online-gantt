from django.contrib.auth import get_user_model
from django.forms import ModelChoiceField
from django_select2 import forms as s2forms

from gantt_chart.models import ChartEvent

User = get_user_model()


def make_dynamic_event_select2_field(project_pk: int, label: str = None, required: bool = False):
    if not label:
        label = "Событие"

    return ModelChoiceField(
        queryset=ChartEvent.objects.all(),
        label=label,
        required=required,
        widget=s2forms.ModelSelect2Widget(data_url=f"/event_select2/?project={project_pk}"),
    )


def make_dynamic_participant_select2_field(project_pk: int, label: str = None, required: bool = False):
    if not label:
        label = "Участник проекта"

    return ModelChoiceField(
        queryset=User.objects.all(),
        label=label,
        required=required,
        widget=s2forms.ModelSelect2Widget(data_url=f"/participant_select2/?project={project_pk}"),
    )
