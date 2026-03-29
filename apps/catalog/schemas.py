from __future__ import annotations

from ninja import Schema

from common.api_schemas import (
    CategoryCardSchema,
    FAQSchema,
    MediaAssetSchema,
    ProductBreadcrumbSchema,
    ProductSummarySchema,
    RelatedResourceSchema,
)


class ProductCategoryDetailSchema(Schema):
    id: int
    name: str
    slug: str
    url_path: str
    h1: str
    lead_text: str
    seo_title: str
    meta_description: str
    summary: str
    buyer_fit: str
    selection_guide: str
    is_core_category: bool
    products: list[ProductSummarySchema]


class ProductVariantSchema(Schema):
    id: int
    name: str
    code: str
    voltage: str
    market: str
    summary: str
    is_default: bool


class ProductSpecRowSchema(Schema):
    id: int
    label: str
    value: str
    unit: str
    is_highlight: bool


class ProductSpecGroupSchema(Schema):
    id: int
    title: str
    group_kind_code: str
    rows: list[ProductSpecRowSchema]


class ProductFeatureSchema(Schema):
    id: int
    title: str
    body: str


class ProductUseCaseSchema(Schema):
    id: int
    title: str
    summary: str


class ProductMediaSchema(Schema):
    id: int
    media_kind: str
    is_primary: bool
    alt_override: str
    asset: MediaAssetSchema | None = None


class ProductDownloadSchema(Schema):
    id: int
    title: str
    download_kind: str
    asset: MediaAssetSchema | None = None


class ProductDetailSchema(Schema):
    id: int
    name: str
    model_code: str
    slug: str
    url_path: str
    h1: str
    lead_text: str
    seo_title: str
    meta_description: str
    summary: str
    buyer_fit: str
    application_summary: str
    buyer_checklist: str
    customization_support: str
    packing_shipping: str
    after_sales_support: str
    quote_cta_title: str
    quote_cta_body: str
    category: CategoryCardSchema
    breadcrumbs: list[ProductBreadcrumbSchema]
    variants: list[ProductVariantSchema]
    quick_facts: list[ProductSpecRowSchema]
    spec_groups: list[ProductSpecGroupSchema]
    features: list[ProductFeatureSchema]
    use_cases: list[ProductUseCaseSchema]
    media_items: list[ProductMediaSchema]
    downloads: list[ProductDownloadSchema]
    related_products: list[ProductSummarySchema]
    related_resources: list[RelatedResourceSchema]
    faq_items: list[FAQSchema]
