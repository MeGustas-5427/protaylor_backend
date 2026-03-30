from __future__ import annotations

from enum import IntEnum

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import ActivatableModel, OrderedModel, SeoFieldsMixin
from common.types import ChoicesMixin


class HomeFeaturedCardType(ChoicesMixin, IntEnum):
    CATEGORY = 1
    RESOURCE = 2
    COMPANY = 3
    SOLUTION = 4

    @classmethod
    def choices(cls):
        names = {
            cls.CATEGORY: "Category",
            cls.RESOURCE: "Resource",
            cls.COMPANY: "Company",
            cls.SOLUTION: "Solution",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.CATEGORY.value: "category",
            cls.RESOURCE.value: "resource",
            cls.COMPANY.value: "company",
            cls.SOLUTION.value: "solution",
        }


class HomeProofKind(ChoicesMixin, IntEnum):
    QUOTE = 1
    LOGO = 2
    CASE = 3

    @classmethod
    def choices(cls):
        names = {
            cls.QUOTE: "Quote",
            cls.LOGO: "Logo",
            cls.CASE: "Case",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.QUOTE.value: "quote",
            cls.LOGO.value: "logo",
            cls.CASE.value: "case",
        }


class SolutionType(ChoicesMixin, IntEnum):
    COMMERCIAL = 1
    SHOP = 2
    OTHER = 3

    @classmethod
    def choices(cls):
        names = {
            cls.COMMERCIAL: "Commercial / Wholesale / OEM",
            cls.SHOP: "Shop / Cafe / Dessert business",
            cls.OTHER: "Other",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.COMMERCIAL.value: "commercial_wholesale_oem",
            cls.SHOP.value: "shop_cafe_dessert_business",
            cls.OTHER.value: "other",
        }


class ResourceType(ChoicesMixin, IntEnum):
    GUIDE = 1
    COMPARISON = 2
    FAQ = 3
    CASE_STUDY = 4
    OTHER = 5

    @classmethod
    def choices(cls):
        names = {
            cls.GUIDE: "Guide",
            cls.COMPARISON: "Comparison",
            cls.FAQ: "FAQ",
            cls.CASE_STUDY: "Case study",
            cls.OTHER: "Other",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.GUIDE.value: "guide",
            cls.COMPARISON.value: "comparison",
            cls.FAQ.value: "faq",
            cls.CASE_STUDY.value: "case_study",
            cls.OTHER.value: "other",
        }


class CompanyPageKind(ChoicesMixin, IntEnum):
    ABOUT = 1
    FACTORY = 2
    CERTIFICATE = 3
    EXPORT = 4
    CONTACT = 5
    OTHER = 6

    @classmethod
    def choices(cls):
        names = {
            cls.ABOUT: "About",
            cls.FACTORY: "Factory",
            cls.CERTIFICATE: "Certificate",
            cls.EXPORT: "Export",
            cls.CONTACT: "Contact",
            cls.OTHER: "Other",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.ABOUT.value: "about",
            cls.FACTORY.value: "factory",
            cls.CERTIFICATE.value: "certificate",
            cls.EXPORT.value: "export",
            cls.CONTACT.value: "contact",
            cls.OTHER.value: "other",
        }


class BasePage(SeoFieldsMixin):
    title = models.CharField(_("页面标题"), max_length=255)
    summary = models.TextField(_("页面摘要"), blank=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.title


class HomeConfig(BasePage, ActivatableModel):
    hero_eyebrow = models.CharField(_("Hero Eyebrow"), max_length=120, blank=True)
    hero_title = models.CharField(_("Hero Title"), max_length=255)
    hero_summary = models.TextField(_("Hero Summary"))
    hero_primary_cta_label = models.CharField(_("主 CTA 标签"), max_length=80, blank=True)
    hero_primary_cta_href = models.CharField(_("主 CTA 链接"), max_length=255, blank=True)
    hero_secondary_cta_label = models.CharField(_("次 CTA 标签"), max_length=80, blank=True)
    hero_secondary_cta_href = models.CharField(_("次 CTA 链接"), max_length=255, blank=True)
    trust_ribbon = models.CharField(_("Trust Ribbon"), max_length=255, blank=True)
    featured_content_heading = models.CharField(_("Featured Heading"), max_length=160, blank=True)
    hero_image = models.ForeignKey(
        "core.MediaAsset",
        verbose_name=_("Hero 背景图"),
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="home_hero_images",
        help_text="首页 Hero 区背景图。",
    )
    value_section_image = models.ForeignKey(
        "core.MediaAsset",
        verbose_name=_("价值区配图"),
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="home_value_images",
        help_text="首页价值点区右侧配图。",
    )

    class Meta:
        db_table = "home_config"
        verbose_name = "首页配置"
        verbose_name_plural = "首页配置"
        constraints = [
            models.UniqueConstraint(fields=("slug",), name="uniq_home_config_slug"),
            models.UniqueConstraint(fields=("url_path",), name="uniq_home_config_path"),
        ]


class HomeBuyerPath(OrderedModel):
    audience_key = models.SlugField(_("Audience Key"), max_length=80)
    title = models.CharField(_("标题"), max_length=160)
    summary = models.TextField(_("摘要"))
    cta_label = models.CharField(_("CTA 标签"), max_length=80)
    cta_href = models.CharField(_("CTA 链接"), max_length=255)
    home = models.ForeignKey(
        HomeConfig,
        verbose_name=_("首页配置"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="buyer_paths",
        help_text="所属首页配置。",
    )
    asset = models.ForeignKey(
        "core.MediaAsset",
        verbose_name=_("背景图"),
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="buyer_path_assets",
        help_text="买家路径卡片背景图。",
    )

    class Meta(OrderedModel.Meta):
        db_table = "home_buyer_path"
        verbose_name = "首页买家路径"
        verbose_name_plural = "首页买家路径"

    def __str__(self) -> str:
        return self.title


class HomeFeaturedCard(OrderedModel):
    CardType = HomeFeaturedCardType

    home = models.ForeignKey(
        HomeConfig,
        verbose_name=_("首页配置"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="featured_cards",
        help_text="所属首页配置。",
    )
    card_type = models.PositiveSmallIntegerField(
        _("卡片类型"),
        choices=HomeFeaturedCardType.choices,
        default=HomeFeaturedCardType.CATEGORY,
        help_text="首页精选卡片类型。",
    )
    eyebrow = models.CharField(_("Eyebrow"), max_length=120, blank=True)
    title = models.CharField(_("标题"), max_length=160)
    summary = models.TextField(_("摘要"))
    cta_label = models.CharField(_("CTA 标签"), max_length=80, blank=True)
    href = models.CharField(_("链接"), max_length=255)
    asset = models.ForeignKey(
        "core.MediaAsset",
        verbose_name=_("媒体资源"),
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="home_feature_cards",
        help_text="卡片配图。允许资源替换或删除后保留卡片记录。",
    )

    class Meta(OrderedModel.Meta):
        db_table = "home_featured_card"
        verbose_name = "首页精选卡片"
        verbose_name_plural = "首页精选卡片"

    @property
    def card_type_code(self) -> str:
        return HomeFeaturedCardType.code_of(self.card_type)

    def __str__(self) -> str:
        return self.title


class HomeProofItem(OrderedModel):
    ProofKind = HomeProofKind

    home = models.ForeignKey(
        HomeConfig,
        verbose_name=_("首页配置"),
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="proof_items",
        help_text="所属首页配置。",
    )
    proof_kind = models.PositiveSmallIntegerField(
        _("证明类型"),
        choices=HomeProofKind.choices,
        default=HomeProofKind.CASE,
        help_text="证明内容类型。",
    )
    title = models.CharField(_("标题"), max_length=160)
    evidence = models.TextField(_("证据文本"))
    source_name = models.CharField(_("来源姓名"), max_length=120, blank=True)
    source_role = models.CharField(_("来源角色"), max_length=120, blank=True)
    href = models.CharField(_("链接"), max_length=255, blank=True)
    asset = models.ForeignKey(
        "core.MediaAsset",
        verbose_name=_("媒体资源"),
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="home_proof_items",
        help_text="证明内容配图。允许资源替换或删除后保留证明项记录。",
    )

    class Meta(OrderedModel.Meta):
        db_table = "home_proof_item"
        verbose_name = "首页证明项"
        verbose_name_plural = "首页证明项"

    @property
    def proof_kind_code(self) -> str:
        return HomeProofKind.code_of(self.proof_kind)

    def __str__(self) -> str:
        return self.title


class SolutionPage(BasePage):
    SolutionType = SolutionType

    solution_type = models.PositiveSmallIntegerField(
        _("解决方案类型"),
        choices=SolutionType.choices,
        default=SolutionType.OTHER,
        db_index=True,
        help_text="解决方案面向的买家路径。",
    )
    body = models.TextField(_("正文"), blank=True)

    class Meta:
        db_table = "solution_page"
        verbose_name = "解决方案页"
        verbose_name_plural = "解决方案页"
        constraints = [
            models.UniqueConstraint(fields=("slug",), name="uniq_solution_page_slug"),
            models.UniqueConstraint(fields=("url_path",), name="uniq_solution_page_path"),
        ]

    @property
    def solution_type_code(self) -> str:
        return SolutionType.code_of(self.solution_type)


class ResourceArticle(BasePage):
    ResourceType = ResourceType

    resource_type = models.PositiveSmallIntegerField(
        _("资源类型"),
        choices=ResourceType.choices,
        default=ResourceType.GUIDE,
        db_index=True,
        help_text="资源内容类型。",
    )
    body = models.TextField(_("正文"), blank=True)

    class Meta:
        db_table = "resource_article"
        verbose_name = "资源文章"
        verbose_name_plural = "资源文章"
        constraints = [
            models.UniqueConstraint(fields=("slug",), name="uniq_resource_article_slug"),
            models.UniqueConstraint(fields=("url_path",), name="uniq_resource_article_path"),
        ]

    @property
    def resource_type_code(self) -> str:
        return ResourceType.code_of(self.resource_type)


class CompanyPage(BasePage):
    PageKind = CompanyPageKind

    page_kind = models.PositiveSmallIntegerField(
        _("公司页面类型"),
        choices=CompanyPageKind.choices,
        default=CompanyPageKind.OTHER,
        db_index=True,
        help_text="公司页面类型。",
    )
    body = models.TextField(_("正文"), blank=True)

    class Meta:
        db_table = "company_page"
        verbose_name = "公司页面"
        verbose_name_plural = "公司页面"
        constraints = [
            models.UniqueConstraint(fields=("slug",), name="uniq_company_page_slug"),
            models.UniqueConstraint(fields=("url_path",), name="uniq_company_page_path"),
        ]

    @property
    def page_kind_code(self) -> str:
        return CompanyPageKind.code_of(self.page_kind)


class FAQItem(OrderedModel):
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("内容类型"),
        on_delete=models.CASCADE,
        db_constraint=False,
        help_text="FAQ 绑定的对象类型。",
    )
    object_id = models.PositiveBigIntegerField(_("对象 ID"))
    content_object = GenericForeignKey("content_type", "object_id")
    question = models.CharField(_("问题"), max_length=255)
    answer = models.TextField(_("答案"))
    is_featured = models.BooleanField(_("是否精选"), default=True)

    class Meta(OrderedModel.Meta):
        db_table = "faq_item"
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"

    def __str__(self) -> str:
        return self.question
