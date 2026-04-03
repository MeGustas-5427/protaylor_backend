from __future__ import annotations

from typing import Iterable

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
    CatalogPaginationSchema,
    ProductCardMetricSchema,
    ProductCategoryDetailSchema,
    ProductCategoryListingResponseSchema,
    ProductDetailSchema,
    ProductDownloadSchema,
    ProductFeatureSchema,
    ProductListingItemSchema,
    ProductMediaSchema,
    ProductPathSchema,
    ProductSpecGroupSchema,
    ProductSpecRowSchema,
    ProductUseCaseSchema,
    ProductVariantSchema,
)
from common.api_schemas import ProductBreadcrumbSchema, RelatedResourceSchema
from common.presenters import serialize_asset, serialize_category_card, serialize_faqs_for, serialize_product_summary
from utils.ninja_pagination import PaginationWindow
from utils.ninja_views import NinjaPaginationMixin

DEFAULT_CATEGORY_PRODUCT_ORDERING = ("name", "id")
CATEGORY_PRODUCT_ORDERING_MAP: dict[str, tuple[str, ...]] = {
    "name": ("name", "id"),
    "name_desc": ("-name", "-id"),
    "newest": ("-created_at", "-id"),
}
LISTING_METRIC_PRIORITY = (
    "production",
    "output",
    "hopper capacity",
    "cylinders",
    "cylinder volume",
    "cooling system",
    "voltage",
    "power",
)
LISTING_METRIC_LIMIT = 3


class CategoryProductListingContract(NinjaPaginationMixin):
    """
    面向 Router 的分类列表查询适配器。

    catalog 对前端暴露的是符号化排序键，而不是裸 ORM 字段。
    用单独的 contract 类包住归一逻辑，可以让 Router 更薄，也让
    分页和排序语义集中在一个可审核的位置。
    """

    DEFAULT_PAGE_SIZE = 12
    MAX_PAGE_SIZE = 100
    DEFAULT_ORDER_BY = ("name",)
    OVERFLOW_STRATEGY = "last"

    def resolve_public_ordering(self, order_by: str | None) -> tuple[str, ...]:
        # 先做 query 归一，再把公开排序键映射到白名单 ORM 排序元组。
        # 这样接口不会泄漏内部字段名，后续底层字段调整时也更容易维护。
        order_key = self.normalize_query(page=1, page_size=self.DEFAULT_PAGE_SIZE, order_by=order_by).order_by[0]
        return CATEGORY_PRODUCT_ORDERING_MAP.get(order_key, DEFAULT_CATEGORY_PRODUCT_ORDERING)


category_product_listing_contract = CategoryProductListingContract()


def _serialize_pagination(window: PaginationWindow) -> CatalogPaginationSchema:
    # 这里故意显式展开字段，而不是直接 `window.__dict__` 整包塞进去。
    # 这样 reviewer 一眼就能看清哪些分页字段是真正对外公开的 API。
    return CatalogPaginationSchema(
        requested_page=window.requested_page,
        current_page=window.current_page,
        page_size=window.page_size,
        total_items=window.total_items,
        total_pages=window.total_pages,
        start_item=window.start_item,
        end_item=window.end_item,
        has_previous=window.has_previous,
        has_next=window.has_next,
    )


def _resolve_category_product_ordering(order_by: str | None) -> tuple[str, ...]:
    return category_product_listing_contract.resolve_public_ordering(order_by)


def _format_spec_row_value(row: ProductSpecRow) -> str:
    return f"{row.value} {row.unit}".strip()


def _iter_listing_rows(product: Product) -> Iterable[ProductSpecRow]:
    """
    Yield prefetched spec rows in display order.

    Listing cards only need a compact subset of technical facts, so we walk the
    already-prefetched groups instead of issuing per-product follow-up queries.
    """

    for group in getattr(product, "listing_spec_groups", []):
        for row in getattr(group, "ordered_rows", []):
            yield row


def _serialize_listing_metrics(product: Product) -> list[ProductCardMetricSchema]:
    highlighted_rows = [row for row in _iter_listing_rows(product) if row.is_highlight]
    candidate_rows = highlighted_rows or list(_iter_listing_rows(product))
    metrics: list[ProductCardMetricSchema] = []
    used_row_ids: set[int] = set()

    # 优先返回买家在列表页最先关心的事实：产能、容量、制冷/供电能力。
    # 这个优先级由后端统一决定，前端不需要再猜哪些规格更适合做卡片指标。
    for preferred_label in LISTING_METRIC_PRIORITY:
        for row in candidate_rows:
            if row.id in used_row_ids:
                continue
            if row.label.strip().lower() != preferred_label:
                continue
            metrics.append(ProductCardMetricSchema(label=row.label, value=_format_spec_row_value(row)))
            used_row_ids.add(row.id)
            if len(metrics) >= LISTING_METRIC_LIMIT:
                return metrics
            break

    for row in candidate_rows:
        if row.id in used_row_ids:
            continue
        metrics.append(ProductCardMetricSchema(label=row.label, value=_format_spec_row_value(row)))
        if len(metrics) >= LISTING_METRIC_LIMIT:
            break

    return metrics


def _resolve_listing_media(product: Product) -> tuple[str, str]:
    """
    Pick a stable card image without asking the frontend to infer media rules.

    The queryset is already ordered with primary media first, so the first valid
    asset is the canonical listing card image.
    """

    for media_item in getattr(product, "listing_media_items", []):
        if not media_item.asset:
            continue
        alt_text = media_item.alt_override or media_item.asset.alt_text or product.name
        return media_item.asset.file_url, alt_text
    return "", product.name


def _serialize_listing_item(product: Product) -> ProductListingItemSchema:
    image_url, image_alt = _resolve_listing_media(product)

    return ProductListingItemSchema(
        id=product.id,
        name=product.name,
        slug=product.slug,
        url_path=product.url_path,
        model_code=product.model_code or "",
        summary=product.summary or product.lead_text or "",
        card_image_url=image_url,
        card_image_alt=image_alt,
        # 这些字段给后续运营编排/货架规则预留。
        # 当前返回 None 是刻意选择，不是遗漏；这样接口形状先稳定下来，
        # 又不会为了凑字段而伪造业务数据。
        series_label=None,
        badge_label=None,
        badge_tone=None,
        metrics=_serialize_listing_metrics(product),
    )


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


def get_category_product_listing(
    slug: str,
    *,
    page: int = 1,
    page_size: int = 12,
    order_by: str | None = None,
) -> ProductCategoryListingResponseSchema:
    """
    构建已发布分类的 PLP 响应契约。

    这个 service 会同时返回分类页头所需内容和分页产品网格，目的是让
    前端列表页只靠一次请求就能完成渲染，同时又不把 guide 页的深内容
    混进列表接口。
    """

    category = (
        ProductCategory.objects.filter(
            slug=slug,
            status=ProductCategory.Status.PUBLISHED,
        )
        .only(
            "id",
            "name",
            "slug",
            "url_path",
            "h1",
            "lead_text",
            "seo_title",
            "meta_description",
            "summary",
        )
        .first()
    )
    if not category:
        raise HttpError(404, "Product category not found.")

    queryset = (
        Product.objects.filter(
            category=category,
            status=Product.Status.PUBLISHED,
            is_canonical=True,
        )
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "media_items",
                queryset=ProductMedia.objects.select_related("asset").order_by("-is_primary", "sort_order", "id"),
                to_attr="listing_media_items",
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
                to_attr="listing_spec_groups",
            ),
        )
        .order_by(*_resolve_category_product_ordering(order_by))
    )

    # 所有 query 归一都走专门的 contract helper，确保公开分页语义只在
    # 一个地方定义，避免 Router、service、前端各自实现一套规则。
    normalized_query = category_product_listing_contract.normalize_query(
        page=page,
        page_size=page_size,
        order_by=order_by,
    )
    page_obj, window = category_product_listing_contract.paginate_objects(
        queryset,
        page=normalized_query.requested_page,
        page_size=normalized_query.page_size,
    )

    return ProductCategoryListingResponseSchema(
        id=category.id,
        name=category.name,
        slug=category.slug,
        url_path=category.url_path,
        h1=category.h1,
        lead_text=category.lead_text or "",
        seo_title=category.seo_title,
        meta_description=category.meta_description,
        summary=category.summary or "",
        pagination=_serialize_pagination(window),
        items=[_serialize_listing_item(product) for product in page_obj.object_list],
    )


def list_product_paths() -> list[ProductPathSchema]:
    """
    返回前端静态路由生成所需的最小路径身份信息。

    把这个 payload 控制得很小，可以避免构建期路由发现和产品详情 schema
    发生不必要耦合。
    """

    queryset = (
        Product.objects.filter(
            status=Product.Status.PUBLISHED,
            is_canonical=True,
            category__status=ProductCategory.Status.PUBLISHED,
        )
        .select_related("category")
        .only("slug", "category__slug")
        .order_by("category__slug", "slug")
    )

    return [
        ProductPathSchema(
            category_slug=product.category.slug,
            product_slug=product.slug,
        )
        for product in queryset
    ]


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
                group_kind_code=group.group_kind_code,
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
