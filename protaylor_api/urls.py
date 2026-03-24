from django.contrib import admin
from django.http import JsonResponse
from django.urls import path

from .api import api


def healthcheck(_: object) -> JsonResponse:
    return JsonResponse({"status": "ok", "service": "protaylor-api"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("healthz/", healthcheck),
]
