from __future__ import annotations

from typing import Any

from django.core.paginator import Page

from utils.ninja_pagination import OverflowStrategy, PaginationWindow, apaginate_queryset
from utils.ninja_views import NinjaListQuery, NinjaPaginationMixin


class NinjaAsyncPaginationMixin(NinjaPaginationMixin):
    """
    Async companion to `NinjaPaginationMixin`.

    Keeping the async adapter in its own file mirrors the separation already
    present in the legacy stack (`views.py` vs `async_views.py`) without
    coupling Ninja endpoints to Django CBV internals.
    """

    async def apaginate_objects(
        self,
        objects: Any,
        *,
        page: int,
        page_size: int,
        overflow: OverflowStrategy | None = None,
    ) -> tuple[Page[Any], PaginationWindow]:
        return await apaginate_queryset(
            objects,
            page=page,
            page_size=page_size,
            overflow=overflow or self.OVERFLOW_STRATEGY,
        )


__all__ = ["NinjaAsyncPaginationMixin", "NinjaListQuery"]
