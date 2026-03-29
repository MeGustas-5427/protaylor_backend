from __future__ import annotations

from django.db.models import Prefetch
from ninja.errors import HttpError

from apps.catalog.models import (
    Product,
    ProductCategory,
    ProductDownload,
    ProductFeature,
    ProductMedia,
    ProductRelation,
    ProductSpecGroup,
    ProductSpecRow,
    ProductUseCase,
    ProductVariant,
)
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
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(status=ProductVariant.Status.PUBLISHED).order_by(
                    "sort_order", "id"
                ),
                to_attr="published_variants",
            ),
            Prefetch(
                "spec_groups",
                queryset=ProductSpecGroup.objects.order_by("sort_order", "id").prefetch_related(
                    Prefetch(
                        "rows",
                        queryset=ProductSpecRow.objects.order_by("sort_order", "id"),
                        to_attr="ordered_rows",
                    )
                ),
                to_attr="ordered_spec_groups",
            ),
            Prefetch(
                "features",
                queryset=ProductFeature.objects.order_by("sort_order", "id"),
                to_attr="ordered_features",
            ),
            Prefetch(
                "use_cases",
                queryset=ProductUseCase.objects.order_by("sort_order", "id"),
                to_attr="ordered_use_cases",
            ),
            Prefetch(
                "media_items",
                queryset=ProductMedia.objects.select_related("asset").order_by("sort_order", "id"),
                to_attr="ordered_media_items",
            ),
            Prefetch(
                "downloads",
                queryset=ProductDownload.objects.select_related("asset").order_by("sort_order", "id"),
                to_attr="ordered_downloads",
            ),
            Prefetch(
                "product_relations",
                queryset=ProductRelation.objects.filter(
                    relation_type=ProductRelation.RelationType.RELATED_PRODUCT,
                    related_product__isnull=False,
                    related_product__status=Product.Status.PUBLISHED,
                    related_product__is_canonical=True,
                )
                .select_related("related_product")
                .order_by("sort_order", "id"),
                to_attr="related_product_relations",
            ),
            Prefetch(
                "product_relations",
                queryset=ProductRelation.objects.filter(
                    relation_type=ProductRelation.RelationType.RELATED_RESOURCE,
                    related_resource__isnull=False,
                    related_resource__status=Product.Status.PUBLISHED,
                )
                .select_related("related_resource")
                .order_by("sort_order", "id"),
                to_attr="related_resource_relations",
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

    related_products = [relation.related_product for relation in product.related_product_relations if relation.related_product]
    related_resources = [
        relation.related_resource for relation in product.related_resource_relations if relation.related_resource
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
            for variant in product.published_variants
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
                    for row in group.ordered_rows
                ],
            )
            for group in product.ordered_spec_groups
        ],
        features=[
            ProductFeatureSchema(id=feature.id, title=feature.title, body=feature.body)
            for feature in product.ordered_features
        ],
        use_cases=[
            ProductUseCaseSchema(id=item.id, title=item.title, summary=item.summary)
            for item in product.ordered_use_cases
        ],
        media_items=[
            ProductMediaSchema(
                id=item.id,
                media_kind=item.media_kind_code,
                is_primary=item.is_primary,
                alt_override=item.alt_override or "",
                asset=serialize_asset(item.asset),
            )
            for item in product.ordered_media_items
        ],
        downloads=[
            ProductDownloadSchema(
                id=item.id,
                title=item.title,
                download_kind=item.download_kind_code,
                asset=serialize_asset(item.asset),
            )
            for item in product.ordered_downloads
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
