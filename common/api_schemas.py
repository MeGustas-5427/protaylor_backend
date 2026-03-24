from __future__ import annotations

from typing import Any

from ninja import Schema


class MediaAssetSchema(Schema):
    id: int
    title: str
    file_url: str
    alt_text: str


class FAQSchema(Schema):
    id: int
    question: str
    answer: str


class CategoryCardSchema(Schema):
    id: int
    name: str
    slug: str
    url_path: str
    summary: str


class ProductSummarySchema(Schema):
    id: int
    name: str
    slug: str
    url_path: str
    model_code: str
    summary: str


class ProductBreadcrumbSchema(Schema):
    title: str
    url_path: str


class RelatedResourceSchema(Schema):
    id: int
    title: str
    slug: str
    url_path: str
    summary: str
    resource_type: str
