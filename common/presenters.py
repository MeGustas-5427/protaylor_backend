from __future__ import annotations

from typing import Any

from django.contrib.contenttypes.models import ContentType

from apps.content.models import FAQItem
from common.api_schemas import (
    CategoryCardSchema,
    FAQSchema,
    MediaAssetSchema,
    ProductSummarySchema,
)


def serialize_asset(asset: Any) -> MediaAssetSchema | None:
    if not asset:
        return None
    return MediaAssetSchema(
        id=asset.id,
        title=asset.title,
        file_url=asset.file_url,
        alt_text=asset.alt_text or "",
    )


def serialize_faqs_for(obj: Any) -> list[FAQSchema]:
    content_type = ContentType.objects.get_for_model(obj, for_concrete_model=False)
    faqs = FAQItem.objects.filter(
        content_type=content_type,
        object_id=obj.id,
        is_featured=True,
    ).order_by("sort_order", "id")
    return [FAQSchema(id=faq.id, question=faq.question, answer=faq.answer) for faq in faqs]


def serialize_category_card(category: Any) -> CategoryCardSchema:
    return CategoryCardSchema(
        id=category.id,
        name=category.name,
        slug=category.slug,
        url_path=category.url_path,
        summary=category.summary or "",
    )


def serialize_product_summary(product: Any) -> ProductSummarySchema:
    return ProductSummarySchema(
        id=product.id,
        name=product.name,
        slug=product.slug,
        url_path=product.url_path,
        model_code=product.model_code or "",
        summary=product.summary or "",
    )
