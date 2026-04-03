from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from django.core.paginator import Page

from utils.ninja_pagination import (
    OverflowStrategy,
    PaginationWindow,
    normalize_order_by,
    normalize_page_number,
    normalize_page_size,
    paginate_queryset,
)


@dataclass(frozen=True)
class NinjaListQuery:
    """
    Router-safe normalized query state.

    This object replaces the mutable `self.page / self.page_size / self.order_by`
    pattern used by legacy Django CBVs. It is designed for service-layer
    consumption after a django-ninja Router has already parsed request input.
    """

    requested_page: int
    page_size: int
    order_by: tuple[str, ...]


class NinjaPaginationMixin:
    """
    Reusable sync pagination/filter adapter for django-ninja services.

    We intentionally keep this outside `utils/views.py` because Ninja routers do
    not use the Django `View` lifecycle or `restful.ok(...)` envelopes. This
    mixin provides the parts that are still worth inheriting:

    - query normalization
    - bounded page size handling
    - public order key parsing
    - pagination execution with a configurable overflow strategy
    """

    DEFAULT_PAGE_SIZE = 30
    MAX_PAGE_SIZE = 100
    DEFAULT_ORDER_BY: Sequence[str] = ("-id",)
    OVERFLOW_STRATEGY: OverflowStrategy = "last"

    def normalize_query(
        self,
        *,
        page: Any,
        page_size: Any,
        order_by: str | None,
    ) -> NinjaListQuery:
        return NinjaListQuery(
            requested_page=normalize_page_number(page),
            page_size=normalize_page_size(
                page_size,
                default=self.DEFAULT_PAGE_SIZE,
                maximum=self.MAX_PAGE_SIZE,
            ),
            order_by=normalize_order_by(order_by, self.DEFAULT_ORDER_BY),
        )

    def paginate_objects(
        self,
        objects: Any,
        *,
        page: int,
        page_size: int,
        overflow: OverflowStrategy | None = None,
    ) -> tuple[Page[Any], PaginationWindow]:
        return paginate_queryset(
            objects,
            page=page,
            page_size=page_size,
            overflow=overflow or self.OVERFLOW_STRATEGY,
        )
