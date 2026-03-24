from __future__ import annotations

from enum import IntEnum

from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimeStampedModel
from common.types import ChoicesMixin


class InquiryStatus(ChoicesMixin, IntEnum):
    NEW = 1
    QUALIFIED = 2
    FOLLOW_UP = 3
    CLOSED = 4
    SPAM = 5

    @classmethod
    def choices(cls):
        names = {
            cls.NEW: "New",
            cls.QUALIFIED: "Qualified",
            cls.FOLLOW_UP: "Follow up",
            cls.CLOSED: "Closed",
            cls.SPAM: "Spam",
        }
        return [(member.value, names[member]) for member in cls]

    @classmethod
    def codes(cls):
        return {
            cls.NEW.value: "new",
            cls.QUALIFIED.value: "qualified",
            cls.FOLLOW_UP.value: "follow_up",
            cls.CLOSED.value: "closed",
            cls.SPAM.value: "spam",
        }


class Inquiry(TimeStampedModel):
    InquiryStatus = InquiryStatus

    full_name = models.CharField(_("姓名"), max_length=120)
    email = models.EmailField(_("邮箱"))
    company = models.CharField(_("公司"), max_length=160, blank=True)
    phone = models.CharField(_("电话"), max_length=80, blank=True)
    country = models.CharField(_("国家"), max_length=120, blank=True)
    business_type = models.CharField(_("业务类型"), max_length=120, blank=True)
    target_use_case = models.CharField(_("目标场景"), max_length=160, blank=True)
    message = models.TextField(_("留言"))
    status = models.PositiveSmallIntegerField(
        _("询盘状态"),
        choices=InquiryStatus.choices,
        default=InquiryStatus.NEW,
        db_index=True,
        help_text="询盘流转状态。",
    )
    consent_to_contact = models.BooleanField(_("同意联系"), default=True)

    class Meta:
        db_table = "inquiry"
        ordering = ("-created_at",)
        verbose_name = "询盘"
        verbose_name_plural = "询盘"

    @property
    def status_code(self) -> str:
        return InquiryStatus.code_of(self.status)

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"


class InquirySourceContext(TimeStampedModel):
    inquiry = models.OneToOneField(
        Inquiry,
        verbose_name=_("询盘"),
        on_delete=models.CASCADE,
        related_name="source_context",
        help_text="所属询盘。",
    )
    source_page_type = models.CharField(_("来源页面类型"), max_length=80, blank=True)
    source_page_path = models.CharField(_("来源页面路径"), max_length=255, blank=True)
    source_page_title = models.CharField(_("来源页面标题"), max_length=255, blank=True)
    product = models.ForeignKey(
        "catalog.Product",
        verbose_name=_("产品"),
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="inquiry_contexts",
        help_text="来源产品，可为空以保留历史询盘。",
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        verbose_name=_("产品变体"),
        on_delete=models.SET_NULL,
        db_constraint=False,
        blank=True,
        null=True,
        related_name="inquiry_contexts",
        help_text="来源产品变体，可为空以保留历史询盘。",
    )
    utm_source = models.CharField(_("UTM Source"), max_length=120, blank=True)
    utm_medium = models.CharField(_("UTM Medium"), max_length=120, blank=True)
    utm_campaign = models.CharField(_("UTM Campaign"), max_length=120, blank=True)
    referer = models.URLField(_("Referer"), blank=True)

    class Meta:
        db_table = "inquiry_source_context"
        verbose_name = "询盘来源上下文"
        verbose_name_plural = "询盘来源上下文"

    def __str__(self) -> str:
        return f"Source for inquiry #{self.inquiry_id}"
