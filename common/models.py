from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.enums import IndexMode, PublishStatus


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True, help_text="记录创建时间。")
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True, help_text="记录最后更新时间。")

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    sort_order = models.PositiveIntegerField(
        _("排序值"),
        default=0,
        db_index=True,
        help_text="排序值，越小越靠前。",
    )

    class Meta:
        abstract = True
        ordering = ("sort_order", "id")


class ActivatableModel(models.Model):
    is_active = models.BooleanField(
        _("是否启用"),
        default=True,
        db_index=True,
        help_text="是否启用。关闭后通常表示不在前台展示，但保留历史数据。",
    )

    class Meta:
        abstract = True


class PublishableModel(TimeStampedModel):
    Status = PublishStatus

    status = models.PositiveSmallIntegerField(
        _("发布状态"),
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
        db_index=True,
        help_text="内容发布状态。",
    )
    published_at = models.DateTimeField(_("发布时间"), blank=True, null=True, help_text="正式发布时间。")

    class Meta:
        abstract = True

    @property
    def status_code(self) -> str:
        return PublishStatus.code_of(self.status)

    @property
    def status_label(self) -> str:
        return PublishStatus.label_of(self.status)


class SeoFieldsMixin(PublishableModel):
    IndexMode = IndexMode

    slug = models.SlugField(_("Slug"), max_length=160, help_text="URL 友好标识。")
    url_path = models.CharField(_("URL Path"), max_length=255, help_text="前端 canonical 路径。")
    h1 = models.CharField(_("H1"), max_length=255, help_text="页面主标题。")
    seo_title = models.CharField(_("SEO Title"), max_length=255, help_text="页面 title。")
    meta_description = models.CharField(_("Meta Description"), max_length=320, help_text="页面 meta description。")
    canonical_url = models.URLField(_("Canonical URL"), blank=True, help_text="可选 canonical 绝对地址。")
    index_mode = models.PositiveSmallIntegerField(
        _("索引模式"),
        choices=IndexMode.choices,
        default=IndexMode.INDEX,
        db_index=True,
        help_text="Index 或 noindex。",
    )
    lead_text = models.TextField(
        _("导语"),
        blank=True,
        help_text="用于页面 Hero 标题下的首段导语。应先说明内容适合谁、解决什么问题；不要与摘要重复。",
    )
    primary_query = models.CharField(
        _("主查询词"),
        max_length=160,
        blank=True,
        help_text="SEO/GEO 用的核心目标查询词，不在前台直接展示，用于校准 H1、title、meta 与正文主题。",
    )
    secondary_queries = models.TextField(
        _("次级查询词"),
        blank=True,
        help_text="SEO/GEO 用的次级查询词，每行一个；不在前台直接展示，用于 FAQ、内链、相关资源与内容覆盖规划。",
    )

    class Meta:
        abstract = True

    @property
    def index_mode_code(self) -> str:
        return IndexMode.code_of(self.index_mode)

    @property
    def index_mode_label(self) -> str:
        return IndexMode.label_of(self.index_mode)


SortableModel = OrderedModel
