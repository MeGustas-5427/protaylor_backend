from django.contrib import admin
from django.http import JsonResponse
from django.urls import path
from django.views.static import serve

from protaylor_api import settings
from .api import api


def healthcheck(_: object) -> JsonResponse:
    return JsonResponse({"status": "ok", "service": "protaylor-api"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("healthz/", healthcheck),
]


# 改为强制启用：
urlpatterns += [
    path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
]