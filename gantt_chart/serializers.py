from rest_framework.serializers import CharField, IntegerField, ModelSerializer, SerializerMethodField

from gantt_chart.models import ChartEvent, ProjectParticipant


class ProjectParticipantSerializer(ModelSerializer):
    id = IntegerField(source="participant.id")
    text = CharField(source="participant")

    class Meta:
        model = ProjectParticipant
        fields = ("id", "text")


class EventSerializer(ModelSerializer):
    text = SerializerMethodField()

    def get_text(self, obj: ChartEvent) -> str:
        return str(obj)

    class Meta:
        model = ChartEvent
        fields = ("id", "text")


class ChartEventBaseSerializer(ModelSerializer):
    id = CharField(source="pk")
    progress = IntegerField(source="percentage_completion")
    dependencies = SerializerMethodField()

    def get_dependencies(self, obj: ChartEvent) -> str:
        followers = tuple(obj.followers_links.select_related("follower__id").values_list("id", flat=True))
        if followers:
            return ", ".join([str(follower) for follower in followers])

        return ""

    class Meta:
        model = ChartEvent
        fields = ("id", "name", "start", "end", "progress", "dependencies")


class ChartEventPlannedSerializer(ChartEventBaseSerializer):
    start = CharField(source="planned_start")
    end = CharField(source="planned_end")


class ChartEventActualSerializer(ChartEventBaseSerializer):
    start = SerializerMethodField()
    end = SerializerMethodField()

    def get_start(self, obj: ChartEvent):
        return obj.actual_start if obj.actual_start else obj.get_current_date()

    def get_end(self, obj: ChartEvent):
        return obj.actual_end if obj.actual_end else obj.get_current_date()
