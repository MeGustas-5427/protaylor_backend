from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Sequence

from django.core.paginator import EmptyPage, Page, PageNotAnInteger, Paginator
from django.http import Http404

OverflowStrategy = Literal["last", "404"]


@dataclass(frozen=True)
class PaginationWindow:
    """Normalized pagination state shared by Router responses and legacy views."""

    requested_page: int
    current_page: int
    page_size: int
    total_items: int
    total_pages: int
    start_item: int
    end_item: int
    has_previous: bool
    has_next: bool


def normalize_page_number(raw_page: Any, default: int = 1) -> int:
    """
    Parse a user-supplied page number into the public contract used by the site.

    Invalid values and numbers below 1 are normalized to the first page instead
    of raising, because the caller may be handling a noisy query string.
    """

    try:
        page = int(raw_page)
    except (TypeError, ValueError):
        return default
    return max(default, page)


def normalize_page_size(raw_page_size: Any, default: int = 30, maximum: int = 100) -> int:
    """
    Clamp page size into a bounded range so Router handlers do not need to
    duplicate the same defensive parsing logic.
    """

    try:
        page_size = int(raw_page_size)
    except (TypeError, ValueError):
        return default
    return max(1, min(page_size, maximum))


def normalize_order_by(raw_order_by: str | None, default: Sequence[str]) -> tuple[str, ...]:
    """
    Convert a comma-delimited ordering string into a tuple.

    The helper does not validate field names. App services should still map the
    public order key onto an allow-listed ordering tuple before hitting ORM.
    """

    if not raw_order_by:
        return tuple(default)

    normalized = tuple(part.strip() for part in raw_order_by.split(",") if part.strip())
    return normalized or tuple(default)


def _build_window(page_obj: Page[Any], requested_page: int) -> PaginationWindow:
    paginator = page_obj.paginator
    total_items = paginator.count

    return PaginationWindow(
        requested_page=requested_page,
        current_page=page_obj.number,
        page_size=paginator.per_page,
        total_items=total_items,
        total_pages=paginator.num_pages,
        start_item=page_obj.start_index() if total_items else 0,
        end_item=page_obj.end_index() if total_items else 0,
        has_previous=page_obj.has_previous(),
        has_next=page_obj.has_next(),
    )


def paginate_queryset(
    objects: Any,
    *,
    page: int,
    page_size: int,
    overflow: OverflowStrategy = "last",
) -> tuple[Page[Any], PaginationWindow]:
    """
    Paginate a queryset or list using the same normalization contract everywhere.

    `overflow="last"` matches the B2B catalog UX: stale or oversized page
    numbers should degrade to the last available page instead of pretending the
    category does not exist. Callers that genuinely need a 404 can opt in via
    `overflow="404"`.
    """

    requested_page = normalize_page_number(page)
    normalized_page_size = normalize_page_size(page_size)
    paginator = Paginator(objects, normalized_page_size)

    try:
        page_obj = paginator.page(requested_page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        if overflow == "404":
            raise Http404()
        last_page = paginator.num_pages if paginator.num_pages > 0 else 1
        page_obj = paginator.page(last_page)

    return page_obj, _build_window(page_obj, requested_page=requested_page)


async def apaginate_queryset(
    objects: Any,
    *,
    page: int,
    page_size: int,
    overflow: OverflowStrategy = "last",
) -> tuple[Page[Any], PaginationWindow]:
    """
    Async companion to `paginate_queryset`.

    Django 6 ships `Paginator.apage()`, so async Router handlers can stay
    non-blocking while reusing the same normalization semantics as sync code.
    """

    requested_page = normalize_page_number(page)
    normalized_page_size = normalize_page_size(page_size)
    paginator = Paginator(objects, normalized_page_size)

    try:
        page_obj = await paginator.apage(requested_page)
    except PageNotAnInteger:
        page_obj = await paginator.apage(1)
    except EmptyPage:
        if overflow == "404":
            raise Http404()
        total_pages = await paginator.anum_pages()
        last_page = total_pages if total_pages > 0 else 1
        page_obj = await paginator.apage(last_page)

    return page_obj, _build_window(page_obj, requested_page=requested_page)
