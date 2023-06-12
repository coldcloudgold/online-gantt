from typing import Any

from django.forms.models import model_to_dict

old_value = Any
new_value = Any


class ModelDiffMixin:
    """
    Миксин для отслеживания изменений инстанса модели

    Дополнительная логика:
    1. Eсли явно не определен параметр `update_fields` при сохранении,
    то параметр проставится в соответствии с теми полями, которые были реально изменены
    2. Если нет реально измененных полей, SQL запрос сохранения не будет вызван
    (за счет того, что `update_fields` будет определен как пустой кортеж)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__initial = self._dict
        self.newly_created: bool = False
        self.last_changed_fields = ()

    @property
    def diff(self) -> dict[str, tuple[old_value, new_value]]:
        """
        Словарь, где:
        - Ключ -> поля инстанса (для полей отношений нет постфикса `_id`)
        - Значение -> кортеж из 2 элементов: где 1 - прошлое значение, 2 - текущее значение
        """

        initial_data = self.__initial
        current_data = self._dict
        diffs = [
            (field, (value, current_data[field]))
            for field, value in initial_data.items()
            if value != current_data[field]
        ]
        return dict(diffs)

    @property
    def new_object(self) -> bool:
        """Является ли инстанс новым (опираясь на pk)"""

        return not bool(self.pk)

    @property
    def has_changed(self) -> bool:
        """Eсть ли изменения в полях инстанса"""

        return bool(self.diff)

    @property
    def changed_fields(self) -> tuple[str]:
        """Коллекция имен измененных полей инстанса"""

        return tuple(self.diff.keys())

    def get_field_diff(self, field_name: str) -> tuple[old_value, new_value] | None:
        """
        Разница значений поля инстанса

        Если поле реально изменилось:
        - Вернет кортеж из 2 элементов: где 1 - прошлое значение, 2 - текущее значение

        Иначе:
        - Вернет `None`
        """

        return self.diff.get(field_name)

    def save(self, *args, **kwargs):
        self.newly_created = self._state.adding

        if not self.new_object:
            if not kwargs.get("update_fields"):
                changed_fields = self.changed_fields
                if changed_fields:
                    kwargs["update_fields"] = changed_fields
                else:
                    kwargs["update_fields"] = ()
            self.last_changed_fields = kwargs["update_fields"]
        else:
            self.last_changed_fields = tuple(self._dict)

        data = super().save(*args, **kwargs)
        self.__initial = self._dict

        return data

    @property
    def _dict(self) -> dict[str, Any]:
        """
        Словарь, где:
        - Ключ -> поля инстанса (для полей отношений нет постфикса `_id`)
        - Значение -> значение поля инстанса на текущий момент
        """

        setted_fields = self._clear_relation_postfix(self.__dict__)
        return model_to_dict(self, fields=[field.name for field in self._meta.fields if field.name in setted_fields])

    def _clear_relation_postfix(self, data: dict[str, Any]) -> dict[str, Any]:
        """Метод очищает поля связей модели от постфикса `_id`"""

        return {field if not field.endswith("_id") else field.rstrip("_id"): value for field, value in data.items()}
