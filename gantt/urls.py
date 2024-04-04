from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("select2/", include("django_select2.urls")),
    path("", include("gantt_chart.urls")),
]

if not settings.DEBUG:
    from django.conf.urls import handler400, handler403, handler404, handler500

    handler400 = "gantt_chart.views.bad_request"  # noqa: F811
    handler403 = "gantt_chart.views.permission_denied"  # noqa: F811
    handler404 = "gantt_chart.views.page_not_found"  # noqa: F811
    handler500 = "gantt_chart.views.server_error"  # noqa: F811

else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
