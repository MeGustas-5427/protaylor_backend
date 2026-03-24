from __future__ import annotations

from django.db.models import Prefetch
from ninja.errors import HttpError

from apps.catalog.models import Product, ProductCategory, ProductRelation, ProductSpecRow, ProductVariant
from apps.catalog.schemas import (
    ProductCategoryDetailSchema,
    ProductDetailSchema,
    ProductDownloadSchema,
    ProductFeatureSchema,
    ProductMediaSchema,
    ProductSpecGroupSchema,
    ProductSpecRowSchema,
    ProductUseCaseSchema,
    ProductVariantSchema,
)
from common.api_schemas import ProductBreadcrumbSchema, RelatedResourceSchema
from common.presenters import serialize_asset, serialize_category_card, serialize_faqs_for, serialize_product_summary


def get_category_detail(slug: str) -> ProductCategoryDetailSchema:
    category = (
        ProductCategory.objects.filter(
            slug=slug,
            status=ProductCategory.Status.PUBLISHED,
        )
        .prefetch_related(
            Prefetch(
                "products",
                queryset=Product.objects.filter(status=Product.Status.PUBLISHED, is_canonical=True).order_by("name"),
            )
        )
        .first()
    )
    if not category:
        raise HttpError(404, "Product category not found.")

    return ProductCategoryDetailSchema(
        id=category.id,
        name=category.name,
        slug=category.slug,
        url_path=category.url_path,
        h1=category.h1,
        lead_text=category.lead_text or "",
        seo_title=category.seo_title,
        meta_description=category.meta_description,
        summary=category.summary or "",
        buyer_fit=category.buyer_fit or "",
        selection_guide=category.selection_guide or "",
        is_core_category=category.is_core_category,
        products=[serialize_product_summary(product) for product in category.products.all()],
    )


def get_product_detail(category_slug: str, product_slug: str) -> ProductDetailSchema:
    product = (
        Product.objects.filter(
            category__slug=category_slug,
            slug=product_slug,
            status=Product.Status.PUBLISHED,
            is_canonical=True,
        )
        .select_related("category")
        .prefetch_related(
            "variants",
            "spec_groups__rows",
            "features",
            "use_cases",
            "media_items__asset",
            "downloads__asset",
            Prefetch(
                "product_relations",
                queryset=ProductRelation.objects.select_related("related_product", "related_resource").order_by("sort_order", "id"),
            ),
        )
        .first()
    )
    if not product:
        raise HttpError(404, "Product not found.")

    quick_facts = ProductSpecRow.objects.filter(
        group__product=product,
        is_highlight=True,
    ).select_related("group").order_by("group__sort_order", "sort_order", "id")

    related_products = [
        relation.related_product
        for relation in product.product_relations.all()
        if relation.related_product_id
    ]
    related_resources = [
        relation.related_resource
        for relation in product.product_relations.all()
        if relation.related_resource_id
    ]

    return ProductDetailSchema(
        id=product.id,
        name=product.name,
        model_code=product.model_code or "",
        slug=product.slug,
        url_path=product.url_path,
        h1=product.h1,
        lead_text=product.lead_text or "",
        seo_title=product.seo_title,
        meta_description=product.meta_description,
        summary=product.summary or "",
        buyer_fit=product.buyer_fit or "",
        application_summary=product.application_summary or "",
        buyer_checklist=product.buyer_checklist or "",
        customization_support=product.customization_support or "",
        packing_shipping=product.packing_shipping or "",
        after_sales_support=product.after_sales_support or "",
        quote_cta_title=product.quote_cta_title or "",
        quote_cta_body=product.quote_cta_body or "",
        category=serialize_category_card(product.category),
        breadcrumbs=[
            ProductBreadcrumbSchema(title="Home", url_path="/"),
            ProductBreadcrumbSchema(title="Products", url_path="/products/"),
            ProductBreadcrumbSchema(title=product.category.name, url_path=product.category.url_path),
            ProductBreadcrumbSchema(title=product.name, url_path=product.url_path),
        ],
        variants=[
            ProductVariantSchema(
                id=variant.id,
                name=variant.name,
                code=variant.code,
                voltage=variant.voltage or "",
                market=variant.market or "",
                summary=variant.summary or "",
                is_default=variant.is_default,
            )
            for variant in product.variants.filter(status=ProductVariant.Status.PUBLISHED).order_by("sort_order", "id")
        ],
        quick_facts=[
            ProductSpecRowSchema(
                id=row.id,
                label=row.label,
                value=row.value,
                unit=row.unit or "",
                is_highlight=row.is_highlight,
            )
            for row in quick_facts
        ],
        spec_groups=[
            ProductSpecGroupSchema(
                id=group.id,
                title=group.title,
                group_kind=group.group_kind_code,
                rows=[
                    ProductSpecRowSchema(
                        id=row.id,
                        label=row.label,
                        value=row.value,
                        unit=row.unit or "",
                        is_highlight=row.is_highlight,
                    )
                    for row in group.rows.all().order_by("sort_order", "id")
                ],
            )
            for group in product.spec_groups.all().order_by("sort_order", "id")
        ],
        features=[
            ProductFeatureSchema(id=feature.id, title=feature.title, body=feature.body)
            for feature in product.features.all().order_by("sort_order", "id")
        ],
        use_cases=[
            ProductUseCaseSchema(id=item.id, title=item.title, summary=item.summary)
            for item in product.use_cases.all().order_by("sort_order", "id")
        ],
        media_items=[
            ProductMediaSchema(
                id=item.id,
                media_kind=item.media_kind_code,
                is_primary=item.is_primary,
                alt_override=item.alt_override or "",
                asset=serialize_asset(item.asset),
            )
            for item in product.media_items.all().order_by("sort_order", "id")
        ],
        downloads=[
            ProductDownloadSchema(
                id=item.id,
                title=item.title,
                download_kind=item.download_kind_code,
                asset=serialize_asset(item.asset),
            )
            for item in product.downloads.all().order_by("sort_order", "id")
        ],
        related_products=[serialize_product_summary(item) for item in related_products if item],
        related_resources=[
            RelatedResourceSchema(
                id=item.id,
                title=item.title,
                slug=item.slug,
                url_path=item.url_path,
                summary=item.summary or "",
                resource_type=item.resource_type_code,
            )
            for item in related_resources
            if item
        ],
        faq_items=serialize_faqs_for(product),
    )
