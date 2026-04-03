from __future__ import annotations

from typing import Any

from django.core.paginator import AsyncPage, AsyncPaginator, EmptyPage, PageNotAnInteger
from django.http import Http404

from utils.ninja_pagination import (
    OverflowStrategy,
    PaginationWindow,
    normalize_page_number,
    normalize_page_size,
)


async def _build_window_async(page_obj: AsyncPage, requested_page: int) -> PaginationWindow:
    """
    AsyncPaginator 专用 window builder。

    acount() / anum_pages() 在 apage() 内部已被调用并缓存于 AsyncPaginator._cache_acount
    / _cache_anum_pages，此处重复 await 不触发额外 SQL。
    start_item / end_item 的计算逻辑与 sync Page.start_index() / end_index() 对齐。
    """
    paginator = page_obj.paginator
    total_items = await paginator.acount()
    num_pages = await paginator.anum_pages()

    if total_items == 0:
        start_item = 0
        end_item = 0
    else:
        start_item = (paginator.per_page * (page_obj.number - 1)) + 1
        # 最后一页直接取 total_items（对齐 Django Page.end_index() 处理 orphans 的逻辑）
        end_item = total_items if page_obj.number == num_pages else page_obj.number * paginator.per_page

    return PaginationWindow(
        requested_page=requested_page,
        current_page=page_obj.number,
        page_size=paginator.per_page,
        total_items=total_items,
        total_pages=num_pages,
        start_item=start_item,
        end_item=end_item,
        has_previous=page_obj.number > 1,
        has_next=page_obj.number < num_pages,
    )


async def apaginate_queryset(
    objects: Any,
    *,
    page: int,
    page_size: int,
    overflow: OverflowStrategy = "last",
) -> tuple[AsyncPage, PaginationWindow]:
    """
    使用 AsyncPaginator 的全异步分页实现，无 sync_to_async 包装。

    overflow="last"  — 页码超出范围时回落到最后一页（B2B 目录的默认行为）
    overflow="404"   — 页码超出范围时抛 Http404
    """
    requested_page = normalize_page_number(page)
    normalized_page_size = normalize_page_size(page_size)
    paginator = AsyncPaginator(objects, normalized_page_size)

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

    return page_obj, await _build_window_async(page_obj, requested_page=requested_page)
