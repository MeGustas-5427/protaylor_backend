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
    summary = models.TextField(_("摘要"), blank=True)
    buyer_fit = models.TextField(_("适合谁"), blank=True)
    application_summary = models.TextField(_("应用概述"), blank=True)
    buyer_checklist = models.TextField(_("买家检查项"), blank=True)
    customization_support = models.TextField(_("定制支持"), blank=True)
    packing_shipping = models.TextField(_("包装运输"), blank=True)
    after_sales_support = models.TextField(_("售后支持"), blank=True)
    quote_cta_title = models.CharField(_("询盘标题"), max_length=160, blank=True)
    quote_cta_body = models.TextField(_("询盘说明"), blank=True)
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
