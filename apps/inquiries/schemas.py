from __future__ import annotations

from ninja import Schema
from pydantic import Field


class InquiryCreateSchema(Schema):
    full_name: str
    email: str
    company: str = ""
    phone: str = ""
    country: str = ""
    business_type: str = ""
    target_use_case: str = ""
    message: str
    consent_to_contact: bool = True
    source_page_type: str = ""
    source_page_path: str = ""
    source_page_title: str = ""
    category_slug: str = ""
    product_slug: str = ""
    variant_code: str = ""
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    referer: str = ""


class InquiryAcceptedSchema(Schema):
    inquiry_id: int
    status: str
    message: str


class RevalidateRequestSchema(Schema):
    secret: str
    paths: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source: str = ""
    reason: str = ""


class RevalidateResponseSchema(Schema):
    accepted: bool
    contract_version: str
    message: str
    paths: list[str]
    tags: list[str]
