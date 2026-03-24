from __future__ import annotations

from typing import Any

from ninja import Router

from apps.catalog.schemas import ProductCategoryDetailSchema, ProductDetailSchema
from apps.catalog.services import get_category_detail, get_product_detail

router = Router(tags=["catalog"])


@router.get("/categories/{slug}", response=ProductCategoryDetailSchema)
def get_category(request: Any, slug: str) -> ProductCategoryDetailSchema:
    del request
    return get_category_detail(slug)


@router.get("/products/{category_slug}/{product_slug}", response=ProductDetailSchema)
def get_product(request: Any, category_slug: str, product_slug: str) -> ProductDetailSchema:
    del request
    return get_product_detail(category_slug, product_slug)
