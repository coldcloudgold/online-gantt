from django.contrib import admin
from django.http.request import HttpRequest

from gantt_chart.models import Project, ProjectParticipant


class ProjectParticipantInline(admin.TabularInline):
    model = ProjectParticipant
    extra = 0
    classes = ("collapse",)
    autocomplete_fields = ("participant",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_display_links = ("name",)
    search_fields = ("name",)
    list_filter = ("is_draft",)
    inlines = (ProjectParticipantInline,)
    readonly_fields = ("project_version",)

    def delete_model(self, request: HttpRequest, obj: Project):
        from gantt_chart.signals import post_delete, set_actual_draft_state_from_project_participant
        from gantt_chart.utils import SignalDisconnectContextManager

        with SignalDisconnectContextManager(
            post_delete, ProjectParticipant, set_actual_draft_state_from_project_participant
        ):
            return super().delete_model(request, obj)
