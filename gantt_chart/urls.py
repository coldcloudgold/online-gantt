from django.contrib.auth.decorators import login_required
from django.urls import path, reverse
from django.shortcuts import redirect

from gantt_chart import views
from gantt_chart.constants import EVENT_IDENTIFIER_FIELD, PROJECT_IDENTIFIER_FIELD, TypeDate


def redirect_to_index(request):
    return redirect(reverse(views.ProjectListView._path_name))


urlpatterns = [
    # Главная
    path("/", redirect_to_index),
    # Проекты
    path("index/", login_required(views.ProjectListView.as_view()), name=views.ProjectListView._path_name),
    path("project/create/", login_required(views.ProjectCreateView.as_view()), name=views.ProjectCreateView._path_name),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/",
        login_required(views.ProjectDetailView.as_view()),
        name=views.ProjectDetailView._path_name,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/update/",
        login_required(views.ProjectUpdateView.as_view()),
        name=views.ProjectUpdateView._path_name,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/delete/",
        login_required(views.ProjectDeleteView.as_view()),
        name=views.ProjectDeleteView._path_name,
    ),
    # Участники проекта
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/participant/",
        login_required(views.ProjectParticipantListView.as_view()),
        name=views.ProjectParticipantListView._path_name,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/participant/create/",
        login_required(views.ProjectParticipantCreateView.as_view()),
        name=views.ProjectParticipantCreateView._path_name,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/participant/<int:pk>/update/",
        login_required(views.ProjectParticipantUpdateView.as_view()),
        name=views.ProjectParticipantUpdateView._path_name,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/participant/<int:pk>/delete/",
        login_required(views.ProjectParticipantDeleteView.as_view()),
        name=views.ProjectParticipantDeleteView._path_name,
    ),
    # События
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/event/",
        login_required(views.EventListView.as_view()),
        name=views.EventListView._path_name,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/event/create/",
        login_required(views.event_create_or_update),
        name=views.event_create_or_update._path_name_create,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/event/<int:{EVENT_IDENTIFIER_FIELD}>/update/",
        login_required(views.event_create_or_update),
        name=views.event_create_or_update._path_name_update,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/events/<int:{EVENT_IDENTIFIER_FIELD}>/delete/",
        login_required(views.EventDeleteView.as_view()),
        name=views.EventDeleteView._path_name,
    ),
    # Связи событий
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/events/<int:{EVENT_IDENTIFIER_FIELD}>/link/",
        login_required(views.EventLinkListView.as_view()),
        name=views.EventLinkListView._path_name,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/events/<int:{EVENT_IDENTIFIER_FIELD}>/link/create/",
        login_required(views.EventLinkCreateView.as_view()),
        name=views.EventLinkCreateView._path_name,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/events/<int:{EVENT_IDENTIFIER_FIELD}>/link/<int:pk>/update/",
        login_required(views.EventLinkUpdateView.as_view()),
        name=views.EventLinkUpdateView._path_name,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/events/<int:{EVENT_IDENTIFIER_FIELD}>/link/<int:pk>/delete/",
        login_required(views.EventLinkDeleteView.as_view()),
        name=views.EventLinkDeleteView._path_name,
    ),
    # График
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/chart/<str:type_date>/",
        login_required(views.chart),
        name=views.chart._path_name,
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/chart/planned/data/",
        login_required(views.ChartEventDataListAPIView.as_view(type_date=TypeDate.planned.value)),
        name="chart_data_planned",
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/chart/actual/data/",
        login_required(views.ChartEventDataListAPIView.as_view(type_date=TypeDate.actual.value)),
        name="chart_data_actual",
    ),
    path(
        f"project/<int:{PROJECT_IDENTIFIER_FIELD}>/chart/<str:type_date>/version/",
        login_required(views.version),
        name="chart_version",
    ),
    # Комментарии
    path("comment/<str:object_type>/<str:object_id>/", login_required(views.comment_hanlde), name="comment_create"),
    path(
        "comment/<str:object_type>/<str:object_id>/<int:pk>/",
        login_required(views.comment_hanlde),
        name="comment_delete",
    ),
    # Select2
    path("participant_select2/", login_required(views.ProjectParticipantListAPIView.as_view())),
    path("event_select2/", login_required(views.SelectEventListAPIView.as_view())),
]
