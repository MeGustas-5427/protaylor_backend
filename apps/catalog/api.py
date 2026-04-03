from __future__ import annotations

from typing import Any

from ninja import Query, Router

from apps.catalog.schemas import (
    CategoryProductListQuerySchema,
    ProductCategoryDetailSchema,
    ProductCategoryListingResponseSchema,
    ProductDetailSchema,
    ProductPathSchema,
)
from apps.catalog.services import (
    get_category_detail,
    get_category_product_listing,
    get_product_detail,
    list_product_paths,
)

router = Router(tags=["catalog"])


@router.get("/categories/{slug}", response=ProductCategoryDetailSchema)
def get_category(request: Any, slug: str) -> ProductCategoryDetailSchema:
    # 分类基础信息 / guide 内容与分页列表内容刻意拆开。
    # 前端分类介绍页走这个接口，真正的产品列表和分页走
    # `/categories/{slug}/products`，避免一个接口承担两种页面职责。
    del request
    return get_category_detail(slug)


@router.get("/categories/{slug}/products", response=ProductCategoryListingResponseSchema)
def get_category_products(
    request: Any,
    slug: str,
    query: CategoryProductListQuerySchema = Query(...),
) -> ProductCategoryListingResponseSchema:
    # Router 层故意不做 ORM 查询和业务拼装。
    # 分页归一、排序白名单、卡片序列化都放在 services.py，
    # 这样 transport 层足够薄，后续审核时更容易看清职责边界。
    del request
    return get_category_product_listing(
        slug,
        page=query.page,
        page_size=query.page_size,
        order_by=query.order_by,
    )


@router.get("/products/{category_slug}/{product_slug}", response=ProductDetailSchema)
def get_product(request: Any, category_slug: str, product_slug: str) -> ProductDetailSchema:
    # 产品详情保持独立读取契约，避免列表接口继续膨胀成
    # “所有页面都共用一个超大 payload”的反模式。
    del request
    return get_product_detail(category_slug, product_slug)


@router.get("/products/paths", response=list[ProductPathSchema])
def get_product_paths(request: Any) -> list[ProductPathSchema]:
    # 这个轻量接口只服务前端静态路由生成。
    # 单独拆出来可以避免构建期为了拿 slug 去过度拉取完整详情 payload。
    del request
    return list_product_paths()
