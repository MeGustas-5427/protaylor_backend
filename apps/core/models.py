from __future__ import annotations

from enum import IntEnum

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import ActivatableModel, OrderedModel, SeoFieldsMixin, TimeStampedModel
from common.types import ChoicesMixin


class AssetKind(ChoicesMixin, IntEnum):
    IMAGE = 1
    DOCUMENT = 2
    VIDEO = 3
    OTHER = 4

    @classmethod
    def choices(cls):
        names = {
            cls.IMAGE: "Image",
            cls.DOCUMENT: "Document",
            cls.VIDEO: "Video",
            cls.OTHER: "Other",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.IMAGE.value: "image",
            cls.DOCUMENT.value: "document",
            cls.VIDEO.value: "video",
            cls.OTHER.value: "other",
        }


class ContactChannelType(ChoicesMixin, IntEnum):
    EMAIL = 1
    PHONE = 2
    WHATSAPP = 3
    WECHAT = 4
    LINKEDIN = 5
    FORM = 6
    ADDRESS = 7
    OTHER = 8

    @classmethod
    def choices(cls):
        names = {
            cls.EMAIL: "Email",
            cls.PHONE: "Phone",
            cls.WHATSAPP: "WhatsApp",
            cls.WECHAT: "WeChat",
            cls.LINKEDIN: "LinkedIn",
            cls.FORM: "Form",
            cls.ADDRESS: "Address",
            cls.OTHER: "Other",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.EMAIL.value: "email",
            cls.PHONE.value: "phone",
            cls.WHATSAPP.value: "whatsapp",
            cls.WECHAT.value: "wechat",
            cls.LINKEDIN.value: "linkedin",
            cls.FORM.value: "form",
            cls.ADDRESS.value: "address",
            cls.OTHER.value: "other",
        }


class ContactPlacement(ChoicesMixin, IntEnum):
    HEADER = 1
    FOOTER = 2
    CONTACT_PAGE = 3
    PRODUCT_PAGE = 4
    GLOBAL = 5

    @classmethod
    def choices(cls):
        names = {
            cls.HEADER: "Header",
            cls.FOOTER: "Footer",
            cls.CONTACT_PAGE: "Contact page",
            cls.PRODUCT_PAGE: "Product page",
            cls.GLOBAL: "Global",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.HEADER.value: "header",
            cls.FOOTER.value: "footer",
            cls.CONTACT_PAGE.value: "contact_page",
            cls.PRODUCT_PAGE.value: "product_page",
            cls.GLOBAL.value: "global",
        }


class NavigationLocation(ChoicesMixin, IntEnum):
    PRIMARY = 1
    SECONDARY = 2
    FOOTER = 3

    @classmethod
    def choices(cls):
        names = {
            cls.PRIMARY: "Primary",
            cls.SECONDARY: "Secondary",
            cls.FOOTER: "Footer",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.PRIMARY.value: "primary",
            cls.SECONDARY.value: "secondary",
            cls.FOOTER.value: "footer",
        }


class PageRelationType(ChoicesMixin, IntEnum):
    RELATED = 1
    PARENT = 2
    CHILD = 3
    TRUST = 4
    RESOURCE = 5

    @classmethod
    def choices(cls):
        names = {
            cls.RELATED: "Related",
            cls.PARENT: "Parent",
            cls.CHILD: "Child",
            cls.TRUST: "Trust",
            cls.RESOURCE: "Resource",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.RELATED.value: "related",
            cls.PARENT.value: "parent",
            cls.CHILD.value: "child",
            cls.TRUST.value: "trust",
            cls.RESOURCE.value: "resource",
        }


class OrganizationProfile(TimeStampedModel, ActivatableModel):
    company_name = models.CharField(_("公司名"), max_length=255)
    brand_name = models.CharField(_("品牌名"), max_length=255)
    legal_name = models.CharField(_("法定名称"), max_length=255, blank=True)
    short_description = models.TextField(_("简介"), blank=True)
    headquarters_city = models.CharField(_("城市"), max_length=120, blank=True)
    headquarters_region = models.CharField(_("地区"), max_length=120, blank=True)
    country = models.CharField(_("国家"), max_length=120, default="China")
    founded_year = models.PositiveIntegerField(_("成立年份"), blank=True, null=True)
    primary_email = models.EmailField(_("主邮箱"), blank=True)
    primary_phone = models.CharField(_("主电话"), max_length=80, blank=True)
    website_url = models.URLField(_("官网"), blank=True)
    address = models.CharField(_("地址"), max_length=255, blank=True)
    postal_code = models.CharField(_("邮编"), max_length=32, blank=True)

    class Meta:
        db_table = "organization_profile"
        ordering = ("company_name",)
        verbose_name = "组织资料"
        verbose_name_plural = "组织资料"

    def __str__(self) -> str:
        return self.brand_name or self.company_name


class MediaAsset(TimeStampedModel):
    AssetKind = AssetKind

    title = models.CharField(_("资源标题"), max_length=255)
    asset_kind = models.PositiveSmallIntegerField(
        _("资源类型"),
        choices=AssetKind.choices,
        default=AssetKind.IMAGE,
        db_index=True,
        help_text="结构化媒体类型。",
    )
    file_url = models.URLField(_("资源地址"))
    alt_text = models.CharField(_("Alt 文本"), max_length=255, blank=True)
    mime_type = models.CharField(_("MIME 类型"), max_length=120, blank=True)
    width = models.PositiveIntegerField(_("宽度"), blank=True, null=True)
    height = models.PositiveIntegerField(_("高度"), blank=True, null=True)
    file_size_bytes = models.PositiveBigIntegerField(_("文件大小"), blank=True, null=True)

    class Meta:
        db_table = "media_asset"
        ordering = ("title", "id")
        verbose_name = "媒体资源"
        verbose_name_plural = "媒体资源"

    @property
    def asset_kind_code(self) -> str:
        return AssetKind.code_of(self.asset_kind)

    def __str__(self) -> str:
        return self.title


class ContactChannel(TimeStampedModel, OrderedModel, ActivatableModel):
    ChannelType = ContactChannelType
    Placement = ContactPlacement

    organization = models.ForeignKey(
        OrganizationProfile,
        verbose_name=_("组织"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="contact_channels",
        help_text="联系方式所属组织。",
    )
    channel_type = models.PositiveSmallIntegerField(
        _("联系方式类型"),
        choices=ContactChannelType.choices,
        default=ContactChannelType.EMAIL,
        db_index=True,
        help_text="联系方式类型。",
    )
    placement = models.PositiveSmallIntegerField(
        _("展示位置"),
        choices=ContactPlacement.choices,
        default=ContactPlacement.GLOBAL,
        db_index=True,
        help_text="该联系方式主要出现的位置。",
    )
    label = models.CharField(_("标签"), max_length=120)
    value = models.CharField(_("值"), max_length=255)
    href = models.CharField(_("链接"), max_length=255, blank=True)
    note = models.CharField(_("备注"), max_length=255, blank=True)
    is_primary = models.BooleanField(_("是否主要联系方式"), default=False)

    class Meta(OrderedModel.Meta):
        db_table = "contact_channel"
        verbose_name = "联系方式"
        verbose_name_plural = "联系方式"

    @property
    def channel_type_code(self) -> str:
        return ContactChannelType.code_of(self.channel_type)

    @property
    def placement_code(self) -> str:
        return ContactPlacement.code_of(self.placement)

    def __str__(self) -> str:
        return f"{ContactChannelType.label_of(self.channel_type)}: {self.label}"


class NavigationItem(TimeStampedModel, OrderedModel, ActivatableModel):
    Location = NavigationLocation

    parent = models.ForeignKey(
        "self",
        verbose_name=_("父导航"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="children",
        blank=True,
        null=True,
        help_text="为空时表示顶级导航。",
    )
    label = models.CharField(_("名称"), max_length=120)
    url_path = models.CharField(_("路径"), max_length=255)
    location = models.PositiveSmallIntegerField(
        _("导航位置"),
        choices=NavigationLocation.choices,
        default=NavigationLocation.PRIMARY,
        db_index=True,
        help_text="导航所在区域。",
    )
    open_in_new_tab = models.BooleanField(_("新窗口打开"), default=False)

    class Meta(OrderedModel.Meta):
        db_table = "navigation_item"
        verbose_name = "导航项"
        verbose_name_plural = "导航项"

    @property
    def location_code(self) -> str:
        return NavigationLocation.code_of(self.location)

    def __str__(self) -> str:
        return self.label


class FooterLinkGroup(TimeStampedModel, OrderedModel, ActivatableModel):
    title = models.CharField(_("分组标题"), max_length=120)
    description = models.CharField(_("分组说明"), max_length=255, blank=True)

    class Meta(OrderedModel.Meta):
        db_table = "footer_link_group"
        verbose_name = "页脚链接组"
        verbose_name_plural = "页脚链接组"

    def __str__(self) -> str:
        return self.title


class FooterLink(TimeStampedModel, OrderedModel, ActivatableModel):
    group = models.ForeignKey(
        FooterLinkGroup,
        verbose_name=_("链接组"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="links",
        help_text="所属页脚链接组。",
    )
    label = models.CharField(_("链接名称"), max_length=120)
    url_path = models.CharField(_("路径"), max_length=255)
    open_in_new_tab = models.BooleanField(_("新窗口打开"), default=False)

    class Meta(OrderedModel.Meta):
        db_table = "footer_link"
        verbose_name = "页脚链接"
        verbose_name_plural = "页脚链接"

    def __str__(self) -> str:
        return self.label


class PageSEO(TimeStampedModel):
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("内容类型"),
        on_delete=models.CASCADE,
        db_constraint=False,
        help_text="SEO 扩展绑定的内容类型。",
    )
    object_id = models.PositiveBigIntegerField(_("对象 ID"))
    content_object = GenericForeignKey("content_type", "object_id")
    schema_profile = models.CharField(_("Schema Profile"), max_length=80, blank=True)
    og_title = models.CharField(_("OG Title"), max_length=255, blank=True)
    og_description = models.CharField(_("OG Description"), max_length=320, blank=True)
    og_image = models.ForeignKey(
        MediaAsset,
        verbose_name=_("OG 图片"),
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="seo_og_references",
        help_text="社交分享图。允许图片资源替换或删除后保留 SEO 配置。",
    )
    twitter_title = models.CharField(_("Twitter Title"), max_length=255, blank=True)
    twitter_description = models.CharField(_("Twitter Description"), max_length=320, blank=True)
    robots_directives = models.CharField(_("Robots 指令"), max_length=255, blank=True)

    class Meta:
        db_table = "page_seo"
        verbose_name = "页面 SEO"
        verbose_name_plural = "页面 SEO"
        constraints = [
            models.UniqueConstraint(
                fields=("content_type", "object_id"),
                name="uniq_page_seo_target",
            )
        ]

    def __str__(self) -> str:
        return f"SEO: {self.content_type.app_label}.{self.content_type.model}:{self.object_id}"


class PageRelation(TimeStampedModel, OrderedModel):
    RelationType = PageRelationType

    source_content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("源内容类型"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="page_relation_sources",
    )
    source_object_id = models.PositiveBigIntegerField(_("源对象 ID"))
    source_object = GenericForeignKey("source_content_type", "source_object_id")
    target_content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("目标内容类型"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="page_relation_targets",
    )
    target_object_id = models.PositiveBigIntegerField(_("目标对象 ID"))
    target_object = GenericForeignKey("target_content_type", "target_object_id")
    relation_type = models.PositiveSmallIntegerField(
        _("关系类型"),
        choices=PageRelationType.choices,
        default=PageRelationType.RELATED,
        help_text="页面之间的结构化关系。",
    )
    note = models.CharField(_("备注"), max_length=255, blank=True)

    class Meta(OrderedModel.Meta):
        db_table = "page_relation"
        verbose_name = "页面关系"
        verbose_name_plural = "页面关系"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "source_content_type",
                    "source_object_id",
                    "target_content_type",
                    "target_object_id",
                    "relation_type",
                ),
                name="uniq_page_relation_edge",
            )
        ]

    @property
    def relation_type_code(self) -> str:
        return PageRelationType.code_of(self.relation_type)

    def __str__(self) -> str:
        return f"{self.relation_type_code}: {self.source_content_type} -> {self.target_content_type}"
