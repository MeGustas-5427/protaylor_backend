from __future__ import annotations

from typing import Any

from ninja import NinjaAPI

from apps.catalog.api import router as catalog_router
from apps.content.api import router as content_router
from apps.core.api import router as core_router
from apps.inquiries.api import router as inquiry_router

api = NinjaAPI(
    title="PRO-TAYLOR Backend API",
    version="1.0.0",
    description="Django + django-ninja backend foundation for the PRO-TAYLOR English-main website.",
    urls_namespace="protaylor-api",
)


@api.get("/healthz", tags=["system"])
def api_healthz(request: Any) -> dict[str, str]:
    del request
    return {"status": "ok", "service": "protaylor-api"}


api.add_router("/v1/site/", core_router)
api.add_router("/v1/site/", content_router)
api.add_router("/v1/catalog/", catalog_router)
api.add_router("/v1/inquiries/", inquiry_router)
