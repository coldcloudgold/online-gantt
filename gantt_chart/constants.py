from enum import Enum
from typing import Any

from django.apps import apps

GANTT_CHART_MODELS = {model.__name__: model for model in apps.get_app_config("gantt_chart").get_models()}
PROJECT_IDENTIFIER_FIELD = "project_pk"
EVENT_IDENTIFIER_FIELD = "event_pk"


class ValuesEnumMixin:
    @classmethod
    def values(cls: Enum) -> tuple[Any]:
        return tuple(element.value for element in cls)


class TypeDate(ValuesEnumMixin, Enum):
    planned = "planned"
    actual = "actual"
