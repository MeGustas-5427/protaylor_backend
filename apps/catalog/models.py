from __future__ import annotations

from enum import IntEnum

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import OrderedModel, PublishableModel, SeoFieldsMixin
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


class Product(SeoFieldsMixin):
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
