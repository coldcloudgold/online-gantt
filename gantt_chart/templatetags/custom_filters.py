from datetime import date

from django import template
from django.forms.boundfield import BoundField
from django.utils.safestring import SafeString

from gantt_chart.permissions import ALL_PERMISSIONS

register = template.Library()


@register.filter
def addclass(field, css="form-control"):
    return field.as_widget(attrs={"class": css})


@register.filter
def addclassandid(field):
    checked = field.value()
    auto_id = field.auto_id
    name = auto_id.lstrip("id_")
    _template = SafeString(
        """<input type="checkbox" name="{name}" class="btn-check" id="{auto_id}" {checked}>""".format(
            name=name, auto_id=auto_id, checked="checked" if checked else ""
        )
        + """<label class="btn btn-outline-primary" for="{auto_id}"><h3>✓</h3></label>""".format(auto_id=auto_id)
    )

    return _template


@register.filter
def none_as_dash(field):
    return field if field else "-"


@register.filter
def none_date_as_dash(field, format="%d.%m.%Y"):
    if not field:
        return "-"
    if isinstance(field, date):
        return field.strftime(format)
    else:
        return str(field)


@register.filter
def field_type(field):
    return field.field.widget.__class__.__name__


for permission in ALL_PERMISSIONS:
    register.filter(permission, ALL_PERMISSIONS[permission])
