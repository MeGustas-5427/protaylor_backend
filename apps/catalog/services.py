from __future__ import annotations

import re
from typing import Iterable

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, OuterRef, Prefetch, Q, Subquery
from ninja.errors import HttpError

from apps.catalog.models import (
    Product,
    ProductCategory,
    ProductCategoryComparisonOverview,
    ProductCategoryComparisonRow,
    ProductCategoryFaqItem,
    ProductCategoryGuide,
    ProductCategoryGuideItem,
    ProductCategoryOperationalItem,
    ProductDownload,
    ProductFeature,
    ProductMedia,
    ProductRelation,
    ProductSpecGroup,
    ProductSpecRow,
    ProductUseCase,
    ProductVariant,
)
from apps.content.models import FAQItem, ResourceArticle
from apps.core.models import PageSEO
from apps.catalog.schemas import (
    CategoryComparisonCellSchema,
    CategoryComparisonOverviewSchema,
    CategoryComparisonRowSchema,
    CategoryComparisonSubjectSchema,
    CategoryFaqItemSchema,
    CategoryGuideContentSchema,
    CategoryGuideContextSchema,
    CategoryGuideDecisionFactorSchema,
    CategoryGuideDefinitionCardSchema,
    CategoryGuidePathSchema,
    CategoryGuidePathItemSchema,
    CategoryGuideResourceSchema,
    CategoryGuideTrustMetricSchema,
    CategoryListingActiveSubcategorySchema,
    CategoryOperationalItemSchema,
    CategoryOverviewCardSchema,
    CategoryPathSchema,
    CatalogPaginationSchema,
    ProductCardMetricSchema,
    ProductCategoryDetailSchema,
    ProductCategoryGuideResponseSchema,
    ProductCategoryListingResponseSchema,
    ProductDetailSchema,
    ProductDownloadSchema,
    ProductFeatureSchema,
    ProductListingItemSchema,
    ProductMediaSchema,
    ProductPathSchema,
    RelatedProductCardSchema,
    RelatedResourceCardSchema,
    SubcategoryTabSchema,
    ProductSpecGroupSchema,
    ProductSpecRowSchema,
    ProductUseCaseSchema,
    ProductVariantSchema,
)
from common.api_schemas import FAQSchema, ProductBreadcrumbSchema
from common.presenters import serialize_asset, serialize_category_card, serialize_product_summary
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
RELATED_RESOURCE_EYEBROW = "RESOURCE CENTER"
PRODUCT_DETAIL_FAQ_LIMIT = 3
DEFAULT_OPERATIONAL_FIT_TITLE = "Operational Fit"
DEFAULT_BUYER_REVIEW_FOCUS_TITLE = "Buyer Review Focus"
DEFAULT_SOURCING_FAQ_TITLE = "Sourcing FAQ"


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


def _serialize_category_operational_item(item: ProductCategoryOperationalItem) -> CategoryOperationalItemSchema:
    return CategoryOperationalItemSchema(
        id=item.id,
        section_code=item.section_code,
        title=item.title,
        body=item.body,
        icon=item.icon or "",
        sort_order=item.sort_order,
    )


def _serialize_category_faq_item(item: ProductCategoryFaqItem) -> CategoryFaqItemSchema:
    return CategoryFaqItemSchema(
        id=item.id,
        placement_code=item.placement_code,
        question=item.question,
        answer=item.answer,
        sort_order=item.sort_order,
    )


def _split_paragraphs(value: str) -> list[str]:
    return [paragraph.strip() for paragraph in re.split(r"\n\s*\n", value or "") if paragraph.strip()]


def _split_lines(value: str) -> list[str]:
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def _resolve_guide_item_href(item: ProductCategoryGuideItem) -> str:
    if item.target_category_id and item.target_category:
        return item.target_category.url_path
    if item.target_resource_id and item.target_resource:
        return item.target_resource.url_path
    return item.href or ""


def _serialize_guide_definition_card(item: ProductCategoryGuideItem) -> CategoryGuideDefinitionCardSchema:
    return CategoryGuideDefinitionCardSchema(
        id=item.id,
        item_key=item.item_key,
        role_code=item.eyebrow or item.item_key,
        title=item.title,
        body=item.body or "",
        icon=item.icon or "",
        sort_order=item.sort_order,
    )


def _serialize_guide_context(item: ProductCategoryGuideItem) -> CategoryGuideContextSchema:
    image_url = item.asset.file_url if item.asset_id and item.asset else ""
    image_alt = item.asset_alt or (item.asset.alt_text if item.asset_id and item.asset else "") or item.title
    return CategoryGuideContextSchema(
        id=item.id,
        item_key=item.item_key,
        title=item.title,
        body=item.body or "",
        image_url=image_url,
        image_alt=image_alt,
        sort_order=item.sort_order,
    )


def _serialize_guide_decision_factor(item: ProductCategoryGuideItem) -> CategoryGuideDecisionFactorSchema:
    return CategoryGuideDecisionFactorSchema(
        id=item.id,
        item_key=item.item_key,
        title=item.title,
        body=item.body or "",
        icon=item.icon or "",
        sort_order=item.sort_order,
    )


def _serialize_guide_path_item(item: ProductCategoryGuideItem) -> CategoryGuidePathItemSchema:
    return CategoryGuidePathItemSchema(
        id=item.id,
        item_key=item.item_key,
        step=item.eyebrow or "",
        title=item.title,
        body=item.body or "",
        bullets=_split_lines(item.supporting_points),
        href=_resolve_guide_item_href(item),
        cta_label=item.cta_label or "",
        sort_order=item.sort_order,
    )


def _serialize_guide_trust_metric(item: ProductCategoryGuideItem) -> CategoryGuideTrustMetricSchema:
    return CategoryGuideTrustMetricSchema(
        id=item.id,
        item_key=item.item_key,
        value=item.eyebrow or "",
        label=item.title,
        sort_order=item.sort_order,
    )


def _serialize_guide_resource(item: ProductCategoryGuideItem) -> CategoryGuideResourceSchema:
    return CategoryGuideResourceSchema(
        id=item.id,
        item_key=item.item_key,
        label=item.eyebrow or "",
        title=item.title,
        href=_resolve_guide_item_href(item),
        cta_label=item.cta_label or "",
        sort_order=item.sort_order,
    )


def _load_category_guide_faqs(category: ProductCategory) -> list[CategoryFaqItemSchema]:
    items = getattr(category, "guide_faq_items", None)
    if items is None:
        items = list(
            category.sourcing_faq_items.filter(
                is_active=True,
                placement=ProductCategoryFaqItem.Placement.GUIDE_FAQ,
            )
            .only("id", "category_id", "placement", "question", "answer", "sort_order", "is_active")
            .order_by("sort_order", "id")
        )
    return [_serialize_category_faq_item(item) for item in items]


def _serialize_category_guide_content(guide: ProductCategoryGuide) -> CategoryGuideContentSchema:
    section_items: dict[int, list[ProductCategoryGuideItem]] = {}
    for item in getattr(guide, "active_items", []):
        section_items.setdefault(item.section, []).append(item)

    hero_image_url = guide.hero_image.file_url if guide.hero_image_id and guide.hero_image else ""
    hero_image_alt = guide.hero_image_alt or (
        guide.hero_image.alt_text if guide.hero_image_id and guide.hero_image else ""
    )

    return CategoryGuideContentSchema(
        id=guide.id,
        hero_eyebrow=guide.hero_eyebrow or "",
        hero_title=guide.hero_title or guide.category.name,
        answer_summary=guide.answer_summary or "",
        hero_primary_cta_label=guide.hero_primary_cta_label or "",
        hero_primary_cta_href=guide.hero_primary_cta_href or "",
        hero_secondary_cta_label=guide.hero_secondary_cta_label or "",
        hero_secondary_cta_href=guide.hero_secondary_cta_href or "",
        hero_image_url=hero_image_url,
        hero_image_alt=hero_image_alt or guide.category.name,
        hero_note_title=guide.hero_note_title or "",
        hero_note_copy=guide.hero_note_copy or "",
        hero_note_quote=guide.hero_note_quote or "",
        hero_note_attribution=guide.hero_note_attribution or "",
        definition_title=guide.definition_title or "",
        definition_copy=guide.definition_copy or "",
        definition_paragraphs=_split_paragraphs(guide.definition_copy),
        definition_cards=[
            _serialize_guide_definition_card(item)
            for item in section_items.get(ProductCategoryGuideItem.Section.DEFINITION_CARD, [])
        ],
        contexts_title=guide.contexts_title or "",
        contexts=[
            _serialize_guide_context(item)
            for item in section_items.get(ProductCategoryGuideItem.Section.OPERATIONAL_CONTEXT, [])
        ],
        matrix_title=guide.matrix_title or "",
        matrix_eyebrow=guide.matrix_eyebrow or "",
        decision_factors=[
            _serialize_guide_decision_factor(item)
            for item in section_items.get(ProductCategoryGuideItem.Section.DECISION_FACTOR, [])
        ],
        paths_title=guide.paths_title or "",
        paths_eyebrow=guide.paths_eyebrow or "",
        paths_mode_code=guide.paths_mode_code,
        paths=[
            _serialize_guide_path_item(item)
            for item in section_items.get(ProductCategoryGuideItem.Section.PATH, [])
        ],
        standards_title=guide.trust_title or "",
        standards_copy=guide.trust_copy or "",
        standards_mode_code=guide.trust_mode_code,
        standards_stats=[
            _serialize_guide_trust_metric(item)
            for item in section_items.get(ProductCategoryGuideItem.Section.TRUST_METRIC, [])
        ],
        faq_title=guide.faq_title or "",
        faqs=_load_category_guide_faqs(guide.category),
        resources_title=guide.resources_title or "",
        resources_mode_code=guide.resources_mode_code,
        resources=[
            _serialize_guide_resource(item)
            for item in section_items.get(ProductCategoryGuideItem.Section.RELATED_RESOURCE, [])
        ],
        cta_title=guide.cta_title or "",
        cta_copy=guide.cta_copy or "",
        cta_mode_code=guide.cta_mode_code,
        cta_primary_label=guide.cta_primary_label or "",
        cta_primary_href=guide.cta_primary_href or "",
        cta_secondary_label=guide.cta_secondary_label or "",
        cta_secondary_href=guide.cta_secondary_href or "",
    )


def _serialize_category_comparison_overview(
    overview: ProductCategoryComparisonOverview,
) -> CategoryComparisonOverviewSchema:
    subjects = sorted(
        overview.subjects_json or [],
        key=lambda item: (int(item.get("sort_order", 0)), str(item.get("subject_key", ""))),
    )
    subject_schemas = [
        CategoryComparisonSubjectSchema(
            subject_key=str(subject["subject_key"]),
            label=str(subject["label"]),
            route_category_slug=str(subject["route_category_slug"]),
            sort_order=int(subject["sort_order"]),
        )
        for subject in subjects
    ]

    row_schemas: list[CategoryComparisonRowSchema] = []
    for row in getattr(overview, "ordered_rows", []):
        cells = [
            CategoryComparisonCellSchema(
                subject_key=subject.subject_key,
                body=str(row.cells_json.get(subject.subject_key, "")),
            )
            for subject in subject_schemas
        ]
        row_schemas.append(
            CategoryComparisonRowSchema(
                row_key=row.row_key,
                label=row.label,
                sort_order=row.sort_order,
                cells=cells,
            )
        )

    return CategoryComparisonOverviewSchema(
        title=overview.title,
        intro=overview.intro or "",
        dimension_heading=overview.dimension_heading,
        subjects=subject_schemas,
        rows=row_schemas,
    )


def _split_category_operational_items(
    items: Iterable[ProductCategoryOperationalItem],
) -> tuple[list[CategoryOperationalItemSchema], list[CategoryOperationalItemSchema]]:
    operational_fit_items: list[CategoryOperationalItemSchema] = []
    buyer_review_focus_items: list[CategoryOperationalItemSchema] = []

    for item in items:
        serialized = _serialize_category_operational_item(item)
        if item.section == ProductCategoryOperationalItem.Section.OPERATIONAL_FIT:
            operational_fit_items.append(serialized)
        elif item.section == ProductCategoryOperationalItem.Section.BUYER_REVIEW_FOCUS:
            buyer_review_focus_items.append(serialized)

    return operational_fit_items, buyer_review_focus_items


def _load_category_sourcing_faq_content(
    category: ProductCategory,
) -> tuple[str, list[CategoryFaqItemSchema]]:
    items = list(
        category.sourcing_faq_items.filter(
            is_active=True,
            placement=ProductCategoryFaqItem.Placement.PLP_SOURCING,
        )
        .only("id", "category_id", "placement", "question", "answer", "sort_order", "is_active")
        .order_by("sort_order", "id")
    )
    return (
        category.sourcing_faq_title or DEFAULT_SOURCING_FAQ_TITLE,
        [_serialize_category_faq_item(item) for item in items],
    )


def _load_category_comparison_overview(
    category: ProductCategory,
) -> CategoryComparisonOverviewSchema | None:
    overview = (
        ProductCategoryComparisonOverview.objects.filter(category=category, is_active=True)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "rows",
                queryset=ProductCategoryComparisonRow.objects.filter(is_active=True).order_by(
                    "sort_order", "id"
                ),
                to_attr="ordered_rows",
            )
        )
        .only("id", "category_id", "title", "intro", "dimension_heading", "subjects_json", "is_active")
        .first()
    )
    if not overview:
        return None
    if not overview.subjects_json:
        return None
    if not getattr(overview, "ordered_rows", []):
        return None
    return _serialize_category_comparison_overview(overview)


def _load_category_operational_content(
    category: ProductCategory,
) -> tuple[
    str,
    list[CategoryOperationalItemSchema],
    str,
    list[CategoryOperationalItemSchema],
]:
    items = list(
        category.operational_items.filter(is_active=True)
        .only("id", "category_id", "section", "title", "body", "icon", "sort_order", "is_active")
        .order_by("section", "sort_order", "id")
    )
    operational_fit_items, buyer_review_focus_items = _split_category_operational_items(items)
    return (
        category.operational_fit_title or DEFAULT_OPERATIONAL_FIT_TITLE,
        operational_fit_items,
        category.buyer_review_focus_title or DEFAULT_BUYER_REVIEW_FOCUS_TITLE,
        buyer_review_focus_items,
    )


def _resolve_category_product_ordering(order_by: str | None) -> tuple[str, ...]:
    return category_product_listing_contract.resolve_public_ordering(order_by)


def _format_spec_row_value(row: ProductSpecRow) -> str:
    return f"{row.value} {row.unit}".strip()


def _serialize_spec_row(row: ProductSpecRow) -> ProductSpecRowSchema:
    return ProductSpecRowSchema(
        id=row.id,
        label=row.label,
        value=row.value,
        unit=row.unit or "",
        is_highlight=row.is_highlight,
    )


def _iter_listing_rows(product: Product) -> Iterable[ProductSpecRow]:
    """
    Yield prefetched spec rows in display order.

    Listing cards only need a compact subset of technical facts, so we walk the
    already-prefetched groups instead of issuing per-product follow-up queries.
    """

    for group in getattr(product, "listing_spec_groups", []):
        for row in getattr(group, "ordered_rows", []):
            yield row


def _iter_detail_rows(product: Product) -> Iterable[ProductSpecRow]:
    for group in getattr(product, "ordered_spec_groups", []):
        for row in getattr(group, "ordered_rows", []):
            yield row


def _serialize_detail_quick_facts(product: Product) -> list[ProductSpecRowSchema]:
    """
    从已经预取好的规格组里提取 Hero quick facts。

    这样可以避免详情页再为高亮规格单独打一条 SQL，同时保持
    `quick_facts` 和 `spec_groups` 使用同一份结构化来源。
    """

    quick_fact_rows = [
        row
        for group in getattr(product, "ordered_spec_groups", [])
        if group.group_kind_code == "quick_facts"
        for row in getattr(group, "ordered_rows", [])
        if row.is_highlight
    ]

    if not quick_fact_rows:
        quick_fact_rows = [row for row in _iter_detail_rows(product) if row.is_highlight]

    return [_serialize_spec_row(row) for row in quick_fact_rows]


def _serialize_product_detail_faqs(product: Product) -> list[FAQSchema]:
    """
    产品详情页需要返回绑定到该 Product 的全部 FAQ。

    这里故意不复用 `common.presenters.serialize_faqs_for()`，因为后者
    当前仍保留“只返回精选 FAQ”的更通用语义；详情页是特例，需要把
    录入在产品下的完整问题集合都交给前端排序和首条默认展开。
    """

    product_content_type = ContentType.objects.get_for_model(product, for_concrete_model=False)
    faqs = FAQItem.objects.filter(
        content_type=product_content_type,
        object_id=product.id,
    ).order_by("sort_order", "id")[:PRODUCT_DETAIL_FAQ_LIMIT]
    return [FAQSchema(id=faq.id, question=faq.question, answer=faq.answer) for faq in faqs]


def _resolve_card_image(image_url: str | None, image_alt: str | None, fallback_alt: str) -> tuple[str, str]:
    return image_url or "", image_alt or fallback_alt


def _serialize_related_product_cards(relations: Iterable[ProductRelation]) -> list[RelatedProductCardSchema]:
    cards: list[RelatedProductCardSchema] = []

    for relation in relations:
        related_product = relation.related_product
        if not related_product:
            continue

        image_url, image_alt = _resolve_card_image(
            getattr(relation, "related_product_image_url", ""),
            getattr(relation, "related_product_image_alt", ""),
            related_product.name,
        )
        cards.append(
            RelatedProductCardSchema(
                id=related_product.id,
                name=related_product.name,
                slug=related_product.slug,
                url_path=related_product.url_path,
                summary=related_product.summary or related_product.lead_text or "",
                eyebrow=related_product.series_label or related_product.category.name,
                image_url=image_url,
                image_alt=image_alt,
            )
        )

    return cards


def _serialize_related_resource_cards(relations: Iterable[ProductRelation]) -> list[RelatedResourceCardSchema]:
    cards: list[RelatedResourceCardSchema] = []

    for relation in relations:
        related_resource = relation.related_resource
        if not related_resource:
            continue

        image_url, image_alt = _resolve_card_image(
            getattr(relation, "related_resource_image_url", ""),
            getattr(relation, "related_resource_image_alt", ""),
            related_resource.title,
        )
        cards.append(
            RelatedResourceCardSchema(
                id=related_resource.id,
                title=related_resource.title,
                slug=related_resource.slug,
                url_path=related_resource.url_path,
                summary=related_resource.summary or related_resource.lead_text or "",
                eyebrow=RELATED_RESOURCE_EYEBROW,
                image_url=image_url,
                image_alt=image_alt,
            )
        )

    return cards


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
        subcategory_slug=product.category.slug,
        subcategory_name=product.category.name,
        card_image_url=image_url,
        card_image_alt=image_alt,
        series_label=product.series_label,
        badge_label=None,
        badge_tone=None,
        metrics=_serialize_listing_metrics(product),
    )


def _get_published_category_or_404(slug: str) -> ProductCategory:
    category = (
        ProductCategory.objects.filter(
            slug=slug,
            status=ProductCategory.Status.PUBLISHED,
        )
        .select_related("parent")
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
            "buyer_fit",
            "selection_guide",
            "operational_fit_title",
            "buyer_review_focus_title",
            "sourcing_faq_title",
            "is_core_category",
            "parent_id",
        )
        .first()
    )
    if not category:
        raise HttpError(404, "Product category not found.")
    return category


def _get_published_child_categories(parent: ProductCategory) -> list[ProductCategory]:
    return list(
        ProductCategory.objects.filter(
            parent=parent,
            status=ProductCategory.Status.PUBLISHED,
        )
        .annotate(
            product_count=Count(
                "products",
                filter=Q(
                    products__status=Product.Status.PUBLISHED,
                    products__is_canonical=True,
                ),
                distinct=True,
            )
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
            "parent_id",
            "operational_fit_title",
            "buyer_review_focus_title",
            "sourcing_faq_title",
        )
        .order_by("name")
    )


def _serialize_subcategory_tabs(categories: list[ProductCategory]) -> list[SubcategoryTabSchema]:
    return [
        SubcategoryTabSchema(
            slug=category.slug,
            name=category.name,
            product_count=getattr(category, "product_count", 0),
        )
        for category in categories
    ]


def _serialize_listing_active_subcategory(
    category: ProductCategory | None,
) -> CategoryListingActiveSubcategorySchema | None:
    if category is None:
        return None

    return CategoryListingActiveSubcategorySchema(
        id=category.id,
        name=category.name,
        slug=category.slug,
        url_path=category.url_path,
        h1=category.h1,
        lead_text=category.lead_text or "",
        seo_title=category.seo_title,
        meta_description=category.meta_description,
        summary=category.summary or "",
    )


def get_category_detail(slug: str) -> ProductCategoryDetailSchema:
    category = _get_published_category_or_404(slug)
    child_categories = _get_published_child_categories(category) if category.parent_id is None else []

    product_filter = Q(category=category)
    if child_categories:
        product_filter = Q(category=category) | Q(category__parent=category)

    products = (
        Product.objects.filter(
            product_filter,
            status=Product.Status.PUBLISHED,
            is_canonical=True,
        )
        .select_related("category")
        .order_by("name")
    )

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
        products=[serialize_product_summary(product) for product in products],
    )


def get_category_guide(slug: str) -> ProductCategoryGuideResponseSchema:
    """
    构建顶级分类 Guide 页响应契约。

    Guide 是独立教育页，不从 PLP 列表 payload 临时拼装；缺少已启用
    Guide 数据时直接返回 404，避免前端静默发布未审核的 fallback 内容。
    """

    guide_item_queryset = (
        ProductCategoryGuideItem.objects.filter(is_active=True)
        .select_related("asset", "target_category", "target_resource")
        .order_by("section", "sort_order", "id")
    )
    guide_faq_queryset = (
        ProductCategoryFaqItem.objects.filter(
            is_active=True,
            placement=ProductCategoryFaqItem.Placement.GUIDE_FAQ,
        )
        .only("id", "category_id", "placement", "question", "answer", "sort_order", "is_active")
        .order_by("sort_order", "id")
    )
    guide = (
        ProductCategoryGuide.objects.filter(
            is_active=True,
            category__slug=slug,
            category__status=ProductCategory.Status.PUBLISHED,
            category__parent__isnull=True,
        )
        .select_related("category", "hero_image")
        .prefetch_related(
            Prefetch("items", queryset=guide_item_queryset, to_attr="active_items"),
            Prefetch("category__sourcing_faq_items", queryset=guide_faq_queryset, to_attr="guide_faq_items"),
        )
        .first()
    )
    if not guide:
        raise HttpError(404, "Product category guide not found.")

    category = guide.category
    return ProductCategoryGuideResponseSchema(
        id=category.id,
        name=category.name,
        slug=category.slug,
        url_path=category.url_path,
        h1=category.h1,
        seo_title=category.seo_title,
        meta_description=category.meta_description,
        guide=_serialize_category_guide_content(guide),
    )


def get_category_product_listing(
    slug: str,
    *,
    page: int = 1,
    page_size: int = 12,
    order_by: str | None = None,
    subcategory_slug: str | None = None,
) -> ProductCategoryListingResponseSchema:
    """
    构建已发布分类的 PLP 响应契约。

    这个 service 会同时返回分类页头所需内容和分页产品网格，目的是让
    前端列表页只靠一次请求就能完成渲染，同时又不把 guide 页的深内容
    混进列表接口。
    """

    category = _get_published_category_or_404(slug)
    child_categories = _get_published_child_categories(category) if category.parent_id is None else []
    active_subcategory_slug: str | None = None
    active_subcategory: ProductCategory | None = None
    subcategory_tabs: list[SubcategoryTabSchema] = []
    operational_content_category: ProductCategory | None = None
    comparison_overview: CategoryComparisonOverviewSchema | None = None
    product_filter = Q(category=category)

    if child_categories:
        child_slug_map = {child.slug: child for child in child_categories}

        if len(child_categories) == 1:
            only_child = child_categories[0]
            if subcategory_slug and subcategory_slug != only_child.slug:
                raise HttpError(400, "Invalid subcategory for this category.")

            # 单子分类父类对前端表现为独立公开分类，因此不返回 tabs；
            # 但当前列表页链路不会切到 child 内容区，只聚合唯一子分类产品，避免 taxonomy 归一后主列表变空。
            active_subcategory_slug = only_child.slug
            product_filter = Q(category=category) | Q(category=only_child)
        else:
            if subcategory_slug:
                selected_child = child_slug_map.get(subcategory_slug)
                if not selected_child:
                    raise HttpError(400, "Invalid subcategory for this category.")
                active_subcategory_slug = selected_child.slug
                active_subcategory = selected_child
                operational_content_category = selected_child
                product_filter = Q(category=selected_child)
            else:
                product_filter = Q(category=category) | Q(category__parent=category)

            subcategory_tabs = _serialize_subcategory_tabs(child_categories)
    elif subcategory_slug:
        raise HttpError(400, "Subcategory filter is not available for this category.")

    queryset = (
        Product.objects.filter(
            status=Product.Status.PUBLISHED,
            is_canonical=True,
        )
        .filter(product_filter)
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

    (
        operational_fit_title,
        operational_fit_items,
        buyer_review_focus_title,
        buyer_review_focus_items,
    ) = _load_category_operational_content(category)
    sourcing_faq_title, sourcing_faq_items = _load_category_sourcing_faq_content(category)
    if operational_content_category is None:
        comparison_overview = _load_category_comparison_overview(category)

    if operational_content_category is not None:
        (
            child_operational_fit_title,
            child_operational_fit_items,
            child_buyer_review_focus_title,
            child_buyer_review_focus_items,
        ) = _load_category_operational_content(operational_content_category)
        child_sourcing_faq_title, child_sourcing_faq_items = _load_category_sourcing_faq_content(
            operational_content_category
        )

        if child_operational_fit_items:
            operational_fit_title = child_operational_fit_title
            operational_fit_items = child_operational_fit_items
        if child_buyer_review_focus_items:
            buyer_review_focus_title = child_buyer_review_focus_title
            buyer_review_focus_items = child_buyer_review_focus_items
        if child_sourcing_faq_items:
            sourcing_faq_title = child_sourcing_faq_title
            sourcing_faq_items = child_sourcing_faq_items

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
        comparison_overview=comparison_overview,
        operational_fit_title=operational_fit_title,
        operational_fit_items=operational_fit_items,
        buyer_review_focus_title=buyer_review_focus_title,
        buyer_review_focus_items=buyer_review_focus_items,
        sourcing_faq_title=sourcing_faq_title,
        sourcing_faq_items=sourcing_faq_items,
        active_subcategory_slug=active_subcategory_slug,
        active_subcategory=_serialize_listing_active_subcategory(active_subcategory),
        subcategory_tabs=subcategory_tabs,
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


def list_category_paths() -> list[CategoryPathSchema]:
    """
    返回前端分类静态路由发现所需的最小路径信息。

    这里只返回 slug 和 url_path，避免把分类 Hero、摘要、产品列表等更重
    的字段混进构建期路径发现流程。
    """

    queryset = (
        ProductCategory.objects.filter(
            status=ProductCategory.Status.PUBLISHED,
            parent__isnull=True,
        )
        .only("slug", "url_path")
        .order_by("name")
    )

    return [CategoryPathSchema(slug=category.slug, url_path=category.url_path) for category in queryset]


def list_category_guide_paths() -> list[CategoryGuidePathSchema]:
    """
    返回 sitemap 可收录的 Guide 页路径。

    这里故意不复用 `list_category_paths()` 后让前端逐个探测 guide 是否存在：
    sitemap 只应该收录已经启用、所属分类已发布、且属于顶级分类的真实 Guide 页。
    """

    queryset = (
        ProductCategoryGuide.objects.filter(
            is_active=True,
            category__status=ProductCategory.Status.PUBLISHED,
            category__parent__isnull=True,
        )
        .select_related("category")
        .only("updated_at", "category__slug", "category__url_path")
        .order_by("category__name")
    )

    return [
        CategoryGuidePathSchema(
            slug=guide.category.slug,
            url_path=guide.category.url_path,
            last_modified=guide.updated_at,
        )
        for guide in queryset
    ]


def list_category_overview_cards() -> list[CategoryOverviewCardSchema]:
    queryset = (
        ProductCategory.objects.filter(
            status=ProductCategory.Status.PUBLISHED,
            parent__isnull=True,
        )
        .annotate(
            direct_product_count=Count(
                "products",
                filter=Q(
                    products__status=Product.Status.PUBLISHED,
                    products__is_canonical=True,
                ),
                distinct=True,
            ),
            child_product_count=Count(
                "children__products",
                filter=Q(
                    children__status=ProductCategory.Status.PUBLISHED,
                    children__products__status=Product.Status.PUBLISHED,
                    children__products__is_canonical=True,
                ),
                distinct=True,
            ),
            published_child_count=Count(
                "children",
                filter=Q(children__status=ProductCategory.Status.PUBLISHED),
                distinct=True,
            ),
        )
        .only("id", "name", "slug", "url_path", "summary", "lead_text")
        .order_by("name")
    )

    return [
        CategoryOverviewCardSchema(
            id=category.id,
            name=category.name,
            slug=category.slug,
            url_path=category.url_path,
            summary=category.summary or "",
            lead_text=category.lead_text or "",
            product_count=category.direct_product_count + category.child_product_count,
            has_children=category.published_child_count > 0,
        )
        for category in queryset
    ]


def get_product_detail(category_slug: str, product_slug: str) -> ProductDetailSchema:
    resource_content_type = ContentType.objects.get_for_model(ResourceArticle, for_concrete_model=False)
    related_product_media_queryset = ProductMedia.objects.filter(
        product_id=OuterRef("related_product_id"),
        asset__isnull=False,
    ).order_by("-is_primary", "sort_order", "id")
    related_resource_seo_queryset = PageSEO.objects.filter(
        content_type=resource_content_type,
        object_id=OuterRef("related_resource_id"),
        og_image__isnull=False,
    ).order_by("id")

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
                queryset=ProductMedia.objects.select_related("asset").order_by("-is_primary", "sort_order", "id"),
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
                .select_related("related_product", "related_product__category")
                .annotate(
                    related_product_image_url=Subquery(related_product_media_queryset.values("asset__file_url")[:1]),
                    related_product_image_alt=Subquery(
                        related_product_media_queryset.values("asset__alt_text")[:1]
                    ),
                )
                .order_by("sort_order", "id"),
                to_attr="related_product_relations",
            ),
            Prefetch(
                "product_relations",
                queryset=ProductRelation.objects.filter(
                    relation_type=ProductRelation.RelationType.RELATED_RESOURCE,
                    related_resource__isnull=False,
                    related_resource__status=ResourceArticle.Status.PUBLISHED,
                )
                .select_related("related_resource")
                .annotate(
                    related_resource_image_url=Subquery(related_resource_seo_queryset.values("og_image__file_url")[:1]),
                    related_resource_image_alt=Subquery(related_resource_seo_queryset.values("og_image__alt_text")[:1]),
                )
                .order_by("sort_order", "id"),
                to_attr="related_resource_relations",
            ),
        )
        .first()
    )
    if not product:
        raise HttpError(404, "Product not found.")

    return ProductDetailSchema(
        id=product.id,
        name=product.name,
        model_code=product.model_code or "",
        slug=product.slug,
        url_path=product.url_path,
        h1=product.h1,
        # Hero eyebrow 仍然表达产品所属分类；series_label 只用于列表和相关产品卡片货架标签。
        hero_eyebrow=product.category.name,
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
        # 这两个字段在现阶段前端并未消费，而且历史数据库与当前 model
        # 定义存在短暂错位，因此这里用 getattr 做向后兼容，避免详情接口
        # 因旧数据或未对齐字段直接报 500。
        quote_cta_title=getattr(product, "quote_cta_title", "") or "",
        quote_cta_body=getattr(product, "quote_cta_body", "") or "",
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
        quick_facts=_serialize_detail_quick_facts(product),
        spec_groups=[
            ProductSpecGroupSchema(
                id=group.id,
                title=group.title,
                group_kind_code=group.group_kind_code,
                rows=[_serialize_spec_row(row) for row in group.ordered_rows],
            )
            for group in product.ordered_spec_groups
        ],
        features=[
            ProductFeatureSchema(id=feature.id, title=feature.title, body=feature.body)
            for feature in product.ordered_features
        ],
        use_cases=[
            ProductUseCaseSchema(
                id=item.id,
                icon=item.icon or "",
                title=item.title,
                summary=item.summary,
            )
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
        related_products=_serialize_related_product_cards(product.related_product_relations),
        related_resources=_serialize_related_resource_cards(product.related_resource_relations),
        faq_items=_serialize_product_detail_faqs(product),
    )
