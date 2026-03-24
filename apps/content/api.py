from __future__ import annotations

from typing import Any

from ninja import Router

from apps.content.schemas import HomeConfigSchema
from apps.content.services import get_home_config

router = Router(tags=["site"])


@router.get("/home", response=HomeConfigSchema)
def get_home(request: Any) -> HomeConfigSchema:
    del request
    return get_home_config()
