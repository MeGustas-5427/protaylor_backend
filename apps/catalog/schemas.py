from __future__ import annotations

from ninja import Schema

from common.api_schemas import (
    CategoryCardSchema,
    FAQSchema,
    MediaAssetSchema,
    ProductBreadcrumbSchema,
    ProductSummarySchema,
)


class CategoryProductListQuerySchema(Schema):
    """
    分类列表页（PLP）查询参数契约。

    这里只暴露 page、page_size 和符号化的排序键，不直接暴露 ORM
    字段名。前端应该依赖稳定的业务语义，而不是数据库实现细节。
    """

    page: int = 1
    page_size: int = 12
    order_by: str | None = None
    subcategory_slug: str | None = None


class CatalogPaginationSchema(Schema):
    """
    前端分类列表页消费的分页元信息。

    同时保留 `requested_page` 和 `current_page`，这样当超界页码被
    归一到最后一页时，前端或边缘层仍然能识别“请求页码”和“实际页码”
    发生了偏差。
    """

    requested_page: int
    current_page: int
    page_size: int
    total_items: int
    total_pages: int
    start_item: int
    end_item: int
    has_previous: bool
    has_next: bool


class ProductCardMetricSchema(Schema):
    """产品卡片上展示的紧凑型技术事实。"""

    label: str
    value: str


class SubcategoryTabSchema(Schema):
    """父分类 PLP 顶部的子分类切换项。"""

    slug: str
    name: str
    product_count: int


class CategoryOperationalItemSchema(Schema):
    """分类列表页 Operational Fit / Buyer Review Focus 结构化条目。"""

    id: int
    section_code: str
    title: str
    body: str
    icon: str
    sort_order: int


class ProductListingItemSchema(Schema):
    """
    分类列表页可直接渲染的产品卡片摘要。

    这个 schema 故意比 `ProductSummarySchema` 更厚，因为列表页需要
    图片和关键指标，不能为了渲染卡片去额外拉每个产品的完整详情。
    """

    id: int
    name: str
    slug: str
    url_path: str
    model_code: str
    summary: str
    subcategory_slug: str
    subcategory_name: str
    card_image_url: str
    card_image_alt: str
    series_label: str | None = None
    badge_label: str | None = None
    badge_tone: str | None = None
    metrics: list[ProductCardMetricSchema]


class ProductCategoryListingResponseSchema(Schema):
    """
    `/products/[categorySlug]` 分类列表页响应契约。

    这里故意重复了一份分类 Hero 所需字段，这样 PLP 可以只请求一个
    payload 就同时拿到页头文案和分页产品网格，而不会把 guide 页的
    深内容混进列表契约里。
    """

    id: int
    name: str
    slug: str
    url_path: str
    h1: str
    lead_text: str
    seo_title: str
    meta_description: str
    summary: str
    operational_fit_title: str
    operational_fit_items: list[CategoryOperationalItemSchema]
    buyer_review_focus_title: str
    buyer_review_focus_items: list[CategoryOperationalItemSchema]
    active_subcategory_slug: str | None = None
    subcategory_tabs: list[SubcategoryTabSchema]
    pagination: CatalogPaginationSchema
    items: list[ProductListingItemSchema]


class ProductPathSchema(Schema):
    """前端静态路由生成所需的最小路径身份信息。"""

    category_slug: str
    product_slug: str


class CategoryPathSchema(Schema):
    """前端分类静态路由生成所需的最小路径身份信息。"""

    slug: str
    url_path: str


class CategoryOverviewCardSchema(Schema):
    """`/products` 顶级分类入口卡片契约。"""

    id: int
    name: str
    slug: str
    url_path: str
    summary: str
    lead_text: str
    product_count: int
    has_children: bool


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
    icon: str
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


class RelatedProductCardSchema(Schema):
    """
    产品详情页“相关推荐产品”卡片契约。

    这里单独建 schema，而不是继续复用 `ProductSummarySchema`，因为详情页
    卡片除了标题和摘要，还需要 eyebrow 与图片。
    """

    id: int
    name: str
    slug: str
    url_path: str
    summary: str
    eyebrow: str
    image_url: str
    image_alt: str


class RelatedResourceCardSchema(Schema):
    """
    产品详情页“相关资源”卡片契约。

    资源卡片的 eyebrow 这轮固定走前端约定语义，但图片与链接仍由后端
    统一给出，避免前端再猜资源卡应该取哪张图。
    """

    id: int
    title: str
    slug: str
    url_path: str
    summary: str
    eyebrow: str
    image_url: str
    image_alt: str


class ProductDetailSchema(Schema):
    id: int
    name: str
    model_code: str
    slug: str
    url_path: str
    h1: str
    hero_eyebrow: str
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
    related_products: list[RelatedProductCardSchema]
    related_resources: list[RelatedResourceCardSchema]
    faq_items: list[FAQSchema]
