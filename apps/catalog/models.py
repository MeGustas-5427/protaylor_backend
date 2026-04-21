from __future__ import annotations

from enum import IntEnum
from typing import Any

from django.core.validators import MaxLengthValidator
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import ActivatableModel, OrderedModel, PublishableModel, SeoFieldsMixin, TimeStampedModel
from common.types import ChoicesMixin


class ProductSpecGroupKind(ChoicesMixin, IntEnum):
    QUICK_FACTS = 1
    TECHNICAL = 2
    UTILITY = 3
    SHIPPING = 4
    OTHER = 5

    @classmethod
    def choices(cls):
        names = {
            cls.QUICK_FACTS: "Quick facts",
            cls.TECHNICAL: "Technical",
            cls.UTILITY: "Utility",
            cls.SHIPPING: "Shipping",
            cls.OTHER: "Other",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.QUICK_FACTS.value: "quick_facts",
            cls.TECHNICAL.value: "technical",
            cls.UTILITY.value: "utility",
            cls.SHIPPING.value: "shipping",
            cls.OTHER.value: "other",
        }


class ProductMediaKind(ChoicesMixin, IntEnum):
    HERO = 1
    GALLERY = 2
    DETAIL = 3
    VIDEO = 4

    @classmethod
    def choices(cls):
        names = {
            cls.HERO: "Hero",
            cls.GALLERY: "Gallery",
            cls.DETAIL: "Detail",
            cls.VIDEO: "Video",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.HERO.value: "hero",
            cls.GALLERY.value: "gallery",
            cls.DETAIL.value: "detail",
            cls.VIDEO.value: "video",
        }


class ProductSeries(ChoicesMixin, IntEnum):
    COUNTERTOP = 1
    INDUSTRIAL = 2

    @classmethod
    def choices(cls):
        names = {
            cls.COUNTERTOP: "COUNTERTOP SERIES",
            cls.INDUSTRIAL: "INDUSTRIAL SERIES",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.COUNTERTOP.value: "countertop",
            cls.INDUSTRIAL.value: "industrial",
        }


class ProductDownloadKind(ChoicesMixin, IntEnum):
    SPEC_SHEET = 1
    CATALOG = 2
    MANUAL = 3
    CERTIFICATE = 4
    OTHER = 5

    @classmethod
    def choices(cls):
        names = {
            cls.SPEC_SHEET: "Spec sheet",
            cls.CATALOG: "Catalog",
            cls.MANUAL: "Manual",
            cls.CERTIFICATE: "Certificate",
            cls.OTHER: "Other",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.SPEC_SHEET.value: "spec_sheet",
            cls.CATALOG.value: "catalog",
            cls.MANUAL.value: "manual",
            cls.CERTIFICATE.value: "certificate",
            cls.OTHER.value: "other",
        }


class ProductRelationType(ChoicesMixin, IntEnum):
    RELATED_PRODUCT = 1
    RELATED_RESOURCE = 2

    @classmethod
    def choices(cls):
        names = {
            cls.RELATED_PRODUCT: "Related product",
            cls.RELATED_RESOURCE: "Related resource",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.RELATED_PRODUCT.value: "related_product",
            cls.RELATED_RESOURCE.value: "related_resource",
        }


class ProductCategoryOperationalSection(ChoicesMixin, IntEnum):
    OPERATIONAL_FIT = 1
    BUYER_REVIEW_FOCUS = 2

    @classmethod
    def choices(cls):
        names = {
            cls.OPERATIONAL_FIT: "Operational Fit",
            cls.BUYER_REVIEW_FOCUS: "Buyer Review Focus",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.OPERATIONAL_FIT.value: "operational_fit",
            cls.BUYER_REVIEW_FOCUS.value: "buyer_review_focus",
        }


class ProductCategoryFaqPlacement(ChoicesMixin, IntEnum):
    PLP_SOURCING = 1
    GUIDE_FAQ = 2

    @classmethod
    def choices(cls):
        names = {
            cls.PLP_SOURCING: "PLP Sourcing FAQ",
            cls.GUIDE_FAQ: "Guide FAQ",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.PLP_SOURCING.value: "plp_sourcing",
            cls.GUIDE_FAQ.value: "guide_faq",
        }


class ProductCategory(SeoFieldsMixin):
    name = models.CharField(_("分类名称"), max_length=255)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("父分类"),
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="children",
        help_text="L2 子分类填写父分类；L1 顶级分类留空。",
    )
    summary = models.TextField(_("摘要"), blank=True)
    buyer_fit = models.TextField(_("适合谁"), blank=True)
    selection_guide = models.TextField(_("选型建议"), blank=True)
    operational_fit_title = models.CharField(
        _("Operational Fit 标题"),
        max_length=120,
        blank=True,
        help_text="用于分类列表页左侧 Operational Fit 模块主标题；为空时前端可回退默认文案。",
    )
    buyer_review_focus_title = models.CharField(
        _("Buyer Review Focus 标题"),
        max_length=120,
        blank=True,
        help_text="用于分类列表页右侧 Buyer Review Focus 模块标题；为空时前端可回退默认文案。",
    )
    sourcing_faq_title = models.CharField(
        _("Sourcing FAQ 标题"),
        max_length=120,
        blank=True,
        help_text="用于分类列表页 Sourcing FAQ 模块标题；为空时前端可回退默认文案。",
    )
    is_core_category = models.BooleanField(_("是否核心分类"), default=False, db_index=True)

    class Meta:
        db_table = "product_category"
        ordering = ("name",)
        verbose_name = "产品分类"
        verbose_name_plural = "产品分类"
        constraints = [
            models.UniqueConstraint(fields=("slug",), name="uniq_product_category_slug"),
            models.UniqueConstraint(fields=("url_path",), name="uniq_product_category_path"),
        ]

    def __str__(self) -> str:
        return self.name


class ProductCategoryOperationalItem(TimeStampedModel, ActivatableModel, OrderedModel):
    Section = ProductCategoryOperationalSection

    category = models.ForeignKey(
        ProductCategory,
        verbose_name=_("所属分类"),
        on_delete=models.CASCADE,
        related_name="operational_items",
        help_text="分类列表页 Operational Fit / Buyer Review Focus 使用的结构化条目。",
    )
    section = models.PositiveSmallIntegerField(
        _("所属分组"),
        choices=ProductCategoryOperationalSection.choices,
        db_index=True,
        help_text="条目属于 Operational Fit 左列，还是 Buyer Review Focus 右列。",
    )
    title = models.CharField(
        _("标题"),
        max_length=32,
        help_text="用于单行标题展示；建议控制在当前 PLP 一行可承载的英文长度内。",
    )
    body = models.CharField(
        _("正文"),
        max_length=120,
        help_text="用于两行正文展示；建议 1-2 句，并控制在当前 PLP 两行可承载的英文长度内。",
    )
    icon = models.CharField(
        _("图标"),
        max_length=40,
        blank=True,
        help_text="Material Icon slug，例如 storefront、bolt、fact_check。",
    )

    class Meta(OrderedModel.Meta):
        db_table = "product_category_operational_item"
        verbose_name = "分类 Operational Fit 条目"
        verbose_name_plural = "分类 Operational Fit 条目"
        constraints = [
            models.UniqueConstraint(
                fields=("category", "section", "sort_order"),
                name="uniq_cat_oper_item_sort",
            )
        ]
        indexes = [
            models.Index(
                fields=("category", "section", "is_active", "sort_order"),
                name="idx_cat_oper_item_q",
            )
        ]

    @property
    def section_code(self) -> str:
        return ProductCategoryOperationalSection.code_of(self.section)

    def __str__(self) -> str:
        return f"{self.category.name}: {self.title}"


class ProductCategoryFaqItem(TimeStampedModel, ActivatableModel, OrderedModel):
    Placement = ProductCategoryFaqPlacement

    category = models.ForeignKey(
        ProductCategory,
        verbose_name=_("所属分类"),
        on_delete=models.CASCADE,
        related_name="sourcing_faq_items",
        help_text="分类页 FAQ 条目。",
    )
    placement = models.PositiveSmallIntegerField(
        _("展示位置"),
        choices=ProductCategoryFaqPlacement.choices,
        db_index=True,
        help_text="FAQ 属于 PLP sourcing FAQ 还是 guide FAQ。",
    )
    question = models.CharField(
        _("问题"),
        max_length=180,
        help_text="建议 1 句，直接对应买家会问的问题。",
    )
    answer = models.TextField(
        _("答案"),
        help_text="建议 1-3 句，回答要具体、可被搜索和 AI 抽取。",
    )

    class Meta(OrderedModel.Meta):
        db_table = "product_category_faq_item"
        verbose_name = "分类 FAQ 条目"
        verbose_name_plural = "分类 FAQ 条目"
        constraints = [
            models.UniqueConstraint(
                fields=("category", "placement", "sort_order"),
                name="uniq_cat_faq_item_sort",
            )
        ]
        indexes = [
            models.Index(
                fields=("category", "placement", "is_active", "sort_order"),
                name="idx_cat_faq_item_q",
            )
        ]

    @property
    def placement_code(self) -> str:
        return ProductCategoryFaqPlacement.code_of(self.placement)

    def __str__(self) -> str:
        return f"{self.category.name}: {self.question}"


class ProductCategoryComparisonOverview(TimeStampedModel, ActivatableModel):
    category = models.OneToOneField(
        ProductCategory,
        verbose_name=_("所属分类"),
        on_delete=models.CASCADE,
        related_name="comparison_overview",
        help_text="分类列表页 Comparison Overview 的模块级配置。",
    )
    title = models.CharField(
        _("模块标题"),
        max_length=160,
        help_text="Comparison Overview 模块标题。",
    )
    intro = models.TextField(
        _("模块导语"),
        blank=True,
        validators=[MaxLengthValidator(220)],
        help_text="Comparison Overview 模块引导语。建议 1-2 句，并控制在 220 个字符以内，避免压坏页面布局。",
    )
    dimension_heading = models.CharField(
        _("维度列表头"),
        max_length=80,
        default="Decision Dimension",
        help_text="对比矩阵第一列表头。",
    )
    subjects_json = models.JSONField(
        _("对比列定义"),
        default=list,
        blank=True,
        help_text=(
            "数组结构，至少包含 subject_key、label、route_category_slug、sort_order。"
        ),
    )

    class Meta:
        db_table = "product_category_comparison_overview"
        verbose_name = "分类 Comparison Overview"
        verbose_name_plural = "分类 Comparison Overview"
        indexes = [
            models.Index(
                fields=("is_active",),
                name="idx_cat_cmp_overview_active",
            )
        ]

    def clean(self) -> None:
        super().clean()
        self.subjects_json = self.validate_subjects_payload(self.subjects_json)
        if self.category_id and self.subjects_json:
            route_slugs = [subject["route_category_slug"] for subject in self.subjects_json]
            route_categories = {
                category.slug: category
                for category in ProductCategory.objects.filter(slug__in=route_slugs).select_related("parent")
            }

            missing_slugs = sorted(set(route_slugs) - set(route_categories.keys()))
            if missing_slugs:
                raise ValidationError(
                    {
                        "subjects_json": (
                            "subjects_json contains unknown route_category_slug values: "
                            + ", ".join(missing_slugs)
                        )
                    }
                )

            invalid_slugs = sorted(
                subject["route_category_slug"]
                for subject in self.subjects_json
                if route_categories[subject["route_category_slug"]].parent_id != self.category_id
            )
            if invalid_slugs:
                raise ValidationError(
                    {
                        "subjects_json": (
                            "subjects_json route_category_slug values must resolve to direct children of "
                            f"{self.category.slug!r}: {', '.join(invalid_slugs)}"
                        )
                    }
                )

    @staticmethod
    def validate_subjects_payload(value: Any) -> list[dict[str, Any]]:
        if value in ("", None):
            return []
        if not isinstance(value, list):
            raise ValidationError({"subjects_json": "subjects_json must be a list."})

        normalized: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        seen_orders: set[int] = set()

        for index, item in enumerate(value, start=1):
            if not isinstance(item, dict):
                raise ValidationError(
                    {"subjects_json": f"subjects_json item {index} must be an object."}
                )

            subject_key = str(item.get("subject_key") or "").strip()
            label = str(item.get("label") or "").strip()
            route_category_slug = str(item.get("route_category_slug") or "").strip()

            if not subject_key:
                raise ValidationError(
                    {"subjects_json": f"subjects_json item {index} requires subject_key."}
                )
            if not label:
                raise ValidationError(
                    {"subjects_json": f"subjects_json item {index} requires label."}
                )
            if not route_category_slug:
                raise ValidationError(
                    {
                        "subjects_json": (
                            f"subjects_json item {index} requires route_category_slug."
                        )
                    }
                )

            sort_order_raw = item.get("sort_order")
            try:
                sort_order = int(sort_order_raw)
            except (TypeError, ValueError) as exc:
                raise ValidationError(
                    {"subjects_json": f"subjects_json item {index} has invalid sort_order."}
                ) from exc

            if subject_key in seen_keys:
                raise ValidationError(
                    {"subjects_json": f"Duplicate subject_key {subject_key!r} is not allowed."}
                )
            if sort_order in seen_orders:
                raise ValidationError(
                    {"subjects_json": f"Duplicate sort_order {sort_order} is not allowed."}
                )

            seen_keys.add(subject_key)
            seen_orders.add(sort_order)
            normalized.append(
                {
                    "subject_key": subject_key,
                    "label": label,
                    "route_category_slug": route_category_slug,
                    "sort_order": sort_order,
                }
            )

        return sorted(normalized, key=lambda item: (item["sort_order"], item["subject_key"]))

    def __str__(self) -> str:
        return f"{self.category.name}: Comparison Overview"


class ProductCategoryComparisonRow(TimeStampedModel, ActivatableModel, OrderedModel):
    overview = models.ForeignKey(
        ProductCategoryComparisonOverview,
        verbose_name=_("所属 Comparison Overview"),
        on_delete=models.CASCADE,
        related_name="rows",
        help_text="Comparison Overview 下的单行对比维度。",
    )
    row_key = models.CharField(
        _("行标识"),
        max_length=80,
        help_text="稳定的业务 key，例如 best_fit_service_format。",
    )
    label = models.CharField(
        _("行标题"),
        max_length=120,
        help_text="对比矩阵左侧行标题。",
    )
    cells_json = models.JSONField(
        _("对比单元格"),
        default=dict,
        blank=True,
        help_text="以 subject_key 为 key、文案为 value 的映射。",
    )

    class Meta(OrderedModel.Meta):
        db_table = "product_category_comparison_row"
        verbose_name = "分类 Comparison Overview 行"
        verbose_name_plural = "分类 Comparison Overview 行"
        constraints = [
            models.UniqueConstraint(
                fields=("overview", "row_key"),
                name="uniq_cat_cmp_row_key",
            ),
            models.UniqueConstraint(
                fields=("overview", "sort_order"),
                name="uniq_cat_cmp_row_sort",
            ),
        ]
        indexes = [
            models.Index(
                fields=("overview", "is_active", "sort_order"),
                name="idx_cat_cmp_row_q",
            )
        ]

    def clean(self) -> None:
        super().clean()
        self.cells_json = self.validate_cells_payload(self.cells_json)
        if self.overview_id and self.overview.subjects_json:
            expected_keys = {subject["subject_key"] for subject in self.overview.subjects_json}
            actual_keys = set(self.cells_json.keys())
            if actual_keys != expected_keys:
                missing = sorted(expected_keys - actual_keys)
                extra = sorted(actual_keys - expected_keys)
                parts: list[str] = []
                if missing:
                    parts.append(f"missing keys: {', '.join(missing)}")
                if extra:
                    parts.append(f"unexpected keys: {', '.join(extra)}")
                raise ValidationError(
                    {
                        "cells_json": (
                            "cells_json keys must match subjects_json exactly; " + "; ".join(parts)
                        )
                    }
                )

    @staticmethod
    def validate_cells_payload(value: Any) -> dict[str, str]:
        if value in ("", None):
            return {}
        if not isinstance(value, dict):
            raise ValidationError({"cells_json": "cells_json must be an object."})

        normalized: dict[str, str] = {}
        for key, body in value.items():
            subject_key = str(key or "").strip()
            if not subject_key:
                raise ValidationError({"cells_json": "cells_json keys must be non-empty strings."})

            body_text = str(body or "").strip()
            if not body_text:
                raise ValidationError(
                    {"cells_json": f"cells_json[{subject_key!r}] must be a non-empty string."}
                )
            normalized[subject_key] = body_text
        return normalized

    def __str__(self) -> str:
        return f"{self.overview.category.name}: {self.label}"


class Product(SeoFieldsMixin):
    Series = ProductSeries

    category = models.ForeignKey(
        ProductCategory,
        verbose_name=_("产品分类"),
        on_delete=models.PROTECT,
        db_constraint=False,
        related_name="products",
        help_text="产品所属分类。",
    )
    name = models.CharField(_("产品名称"), max_length=255)
    model_code = models.CharField(_("型号"), max_length=120, blank=True)
    series = models.PositiveSmallIntegerField(
        _("产品系列"),
        choices=ProductSeries.choices,
        default=ProductSeries.COUNTERTOP,
        db_index=True,
        help_text="用于产品列表和相关推荐卡片的货架标签。",
    )
    summary = models.TextField(
        _("摘要"),
        blank=True,
        help_text="用于产品列表卡、相关推荐卡等摘要展示；不要写成产品详情页 Hero 首段导语。建议 1-2 句。",
    )
    buyer_fit = models.TextField(
        _("适合谁"),
        blank=True,
        help_text="用于“适合谁 / Best fit for”模块。建议每行一个买家类型、门店类型或采购场景。",
    )
    application_summary = models.TextField(
        _("应用概述"),
        blank=True,
        help_text="用于“应用概述 / Applications”模块，解释适用场景、运营环境与典型使用方式；不是 Hero 导语。",
    )
    buyer_checklist = models.TextField(
        _("买家检查项"),
        blank=True,
        help_text="用于“买家检查项 / Before you request a quote”模块。建议每行一个检查项，前端按列表展示。",
    )
    customization_support = models.TextField(
        _("定制支持"),
        blank=True,
        help_text="用于“定制支持”模块，说明 OEM/ODM、品牌、配置定制能力。",
    )
    packing_shipping = models.TextField(
        _("包装运输"),
        blank=True,
        help_text="用于“包装运输”模块，说明包装方式、交期、运输与出口安排。",
    )
    after_sales_support = models.TextField(
        _("售后支持"),
        blank=True,
        help_text="用于“售后支持”模块，说明保修、备件、远程支持与服务响应。",
    )
    source_url = models.URLField(
        _("来源 URL"),
        max_length=500,
        blank=True,
        help_text="Bossgoo 原始产品页链接，仅供数据追溯，不对外展示。",
    )
    raw_description = models.TextField(
        _("原始描述"),
        blank=True,
        help_text="从 Bossgoo 导入的原始描述，仅用于追溯与编辑参考，不在前台直接展示。",
    )
    raw_attributes = models.JSONField(
        _("原始属性"),
        default=dict,
        blank=True,
        help_text=(
            "从 Bossgoo 导入的原始键值属性（对应 Excel B 区 333 个字段中非空的部分）。"
            "此字段为数据存档层，前端展示请使用 ProductSpecGroup/Row。"
        ),
    )
    is_canonical = models.BooleanField(_("是否 canonical"), default=True, db_index=True)
    faq_items = GenericRelation(
        "content.FAQItem",
        related_query_name="product",
        content_type_field="content_type",
        object_id_field="object_id",
    )

    class Meta:
        db_table = "product"
        ordering = ("category__name", "name")
        verbose_name = "产品"
        verbose_name_plural = "产品"
        constraints = [
            models.UniqueConstraint(
                fields=("category", "slug"),
                name="uniq_product_slug_per_category",
            ),
            models.UniqueConstraint(fields=("url_path",), name="uniq_product_path"),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def series_code(self) -> str:
        return ProductSeries.code_of(self.series)

    @property
    def series_label(self) -> str:
        return ProductSeries.label_of(self.series).upper()


class ProductVariant(PublishableModel, OrderedModel):
    product = models.ForeignKey(
        Product,
        verbose_name=_("产品"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="variants",
        help_text="所属产品。",
    )
    name = models.CharField(_("变体名称"), max_length=160)
    code = models.CharField(_("变体编码"), max_length=120)
    voltage = models.CharField(_("电压"), max_length=80, blank=True)
    market = models.CharField(_("市场"), max_length=120, blank=True)
    summary = models.TextField(_("摘要"), blank=True)
    is_default = models.BooleanField(_("是否默认"), default=False)

    class Meta(OrderedModel.Meta):
        db_table = "product_variant"
        verbose_name = "产品变体"
        verbose_name_plural = "产品变体"
        constraints = [
            models.UniqueConstraint(
                fields=("product", "code"),
                name="uniq_product_variant_code",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.code}"


class ProductSpecGroup(OrderedModel):
    GroupKind = ProductSpecGroupKind

    product = models.ForeignKey(
        Product,
        verbose_name=_("产品"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="spec_groups",
        help_text="所属产品。",
    )
    title = models.CharField(_("分组标题"), max_length=160)
    group_kind = models.PositiveSmallIntegerField(
        _("分组类型"),
        choices=ProductSpecGroupKind.choices,
        default=ProductSpecGroupKind.TECHNICAL,
        help_text="规格组类型。",
    )

    class Meta(OrderedModel.Meta):
        db_table = "product_spec_group"
        verbose_name = "规格分组"
        verbose_name_plural = "规格分组"

    @property
    def group_kind_code(self) -> str:
        return ProductSpecGroupKind.code_of(self.group_kind)

    def __str__(self) -> str:
        return f"{self.product.name}: {self.title}"


class ProductSpecRow(OrderedModel):
    group = models.ForeignKey(
        ProductSpecGroup,
        verbose_name=_("规格组"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="rows",
        help_text="所属规格组。",
    )
    label = models.CharField(_("规格名称"), max_length=160)
    value = models.CharField(_("规格值"), max_length=255)
    unit = models.CharField(_("单位"), max_length=40, blank=True)
    is_highlight = models.BooleanField(_("是否高亮"), default=False, db_index=True)

    class Meta(OrderedModel.Meta):
        db_table = "product_spec_row"
        verbose_name = "规格行"
        verbose_name_plural = "规格行"

    def __str__(self) -> str:
        return f"{self.label}: {self.value}"


class ProductFeature(OrderedModel):
    product = models.ForeignKey(
        Product,
        verbose_name=_("产品"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="features",
        help_text="所属产品。",
    )
    title = models.CharField(_("卖点标题"), max_length=160)
    body = models.TextField(_("卖点说明"))

    class Meta(OrderedModel.Meta):
        db_table = "product_feature"
        verbose_name = "产品卖点"
        verbose_name_plural = "产品卖点"

    def __str__(self) -> str:
        return self.title


class ProductUseCase(OrderedModel):
    product = models.ForeignKey(
        Product,
        verbose_name=_("产品"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="use_cases",
        help_text="所属产品。",
    )
    icon = models.CharField(
        _("图标"),
        max_length=60,
        blank=True,
        help_text="Material Icon slug，如 restaurant / hotel / icecream。",
    )
    title = models.CharField(_("场景标题"), max_length=160)
    summary = models.TextField(_("场景说明"))

    class Meta(OrderedModel.Meta):
        db_table = "product_use_case"
        verbose_name = "应用场景"
        verbose_name_plural = "应用场景"

    def __str__(self) -> str:
        return self.title


class ProductMedia(OrderedModel):
    MediaKind = ProductMediaKind

    product = models.ForeignKey(
        Product,
        verbose_name=_("产品"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="media_items",
        help_text="所属产品。",
    )
    asset = models.ForeignKey(
        "core.MediaAsset",
        verbose_name=_("媒体资源"),
        on_delete=models.PROTECT,
        db_constraint=False,
        related_name="product_media_items",
        help_text="关联的媒体资源。",
    )
    media_kind = models.PositiveSmallIntegerField(
        _("媒体类型"),
        choices=ProductMediaKind.choices,
        default=ProductMediaKind.GALLERY,
        help_text="媒体展示类型。",
    )
    is_primary = models.BooleanField(_("是否主图"), default=False)
    alt_override = models.CharField(_("Alt 覆盖"), max_length=255, blank=True)

    class Meta(OrderedModel.Meta):
        db_table = "product_media"
        verbose_name = "产品媒体"
        verbose_name_plural = "产品媒体"

    @property
    def media_kind_code(self) -> str:
        return ProductMediaKind.code_of(self.media_kind)

    def __str__(self) -> str:
        return f"{self.product.name}: {self.asset.title}"


class ProductDownload(OrderedModel):
    DownloadKind = ProductDownloadKind

    product = models.ForeignKey(
        Product,
        verbose_name=_("产品"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="downloads",
        help_text="所属产品。",
    )
    asset = models.ForeignKey(
        "core.MediaAsset",
        verbose_name=_("下载资源"),
        on_delete=models.PROTECT,
        db_constraint=False,
        related_name="product_downloads",
        help_text="关联的下载文件。",
    )
    title = models.CharField(_("下载标题"), max_length=160)
    download_kind = models.PositiveSmallIntegerField(
        _("下载类型"),
        choices=ProductDownloadKind.choices,
        default=ProductDownloadKind.OTHER,
        help_text="下载文件类型。",
    )

    class Meta(OrderedModel.Meta):
        db_table = "product_download"
        verbose_name = "产品下载"
        verbose_name_plural = "产品下载"

    @property
    def download_kind_code(self) -> str:
        return ProductDownloadKind.code_of(self.download_kind)

    def __str__(self) -> str:
        return self.title


class ProductRelation(OrderedModel):
    RelationType = ProductRelationType

    product = models.ForeignKey(
        Product,
        verbose_name=_("产品"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="product_relations",
        help_text="关系的源产品。",
    )
    relation_type = models.PositiveSmallIntegerField(
        _("关系类型"),
        choices=ProductRelationType.choices,
        default=ProductRelationType.RELATED_PRODUCT,
        help_text="相关推荐还是相关资源。",
    )
    related_product = models.ForeignKey(
        Product,
        verbose_name=_("关联产品"),
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="incoming_product_relations",
        help_text="当关系类型为 related_product 时使用。允许关联产品下线后保留当前关系记录。",
    )
    related_resource = models.ForeignKey(
        "content.ResourceArticle",
        verbose_name=_("关联资源"),
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="incoming_product_relations",
        help_text="当关系类型为 related_resource 时使用。允许关联资源下线后保留当前关系记录。",
    )

    class Meta(OrderedModel.Meta):
        db_table = "product_relation"
        verbose_name = "产品关系"
        verbose_name_plural = "产品关系"
        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(relation_type=ProductRelationType.RELATED_PRODUCT)
                        & models.Q(related_product__isnull=False)
                        & models.Q(related_resource__isnull=True)
                    )
                    | (
                        models.Q(relation_type=ProductRelationType.RELATED_RESOURCE)
                        & models.Q(related_product__isnull=True)
                        & models.Q(related_resource__isnull=False)
                    )
                ),
                name="product_relation_matches_target",
            )
        ]

    @property
    def relation_type_code(self) -> str:
        return ProductRelationType.code_of(self.relation_type)

    def __str__(self) -> str:
        return f"{self.product.name}: {self.relation_type_code}"
