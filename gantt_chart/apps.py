from django.apps import AppConfig


class GanttAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gantt_chart"
    verbose_name = "График Гантта"

    def ready(self):
        import gantt_chart.signals
