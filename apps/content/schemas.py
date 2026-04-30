from __future__ import annotations

from ninja import Schema

from common.api_schemas import CategoryCardSchema, FAQSchema, MediaAssetSchema


class HomeBuyerPathSchema(Schema):
    id: int
    audience_key: str
    title: str
    summary: str
    cta_label: str
    cta_href: str


class HomeFeaturedCardSchema(Schema):
    id: int
    card_type_code: str
    title: str
    summary: str
    href: str
    asset: MediaAssetSchema | None = None


class HomeProofItemSchema(Schema):
    id: int
    proof_kind: str
    title: str
    evidence: str
    source_name: str
    source_role: str
    href: str
    asset: MediaAssetSchema | None = None


class HomeConfigSchema(Schema):
    id: int
    title: str
    slug: str
    url_path: str
    h1: str
    lead_text: str
    hero_eyebrow: str
    hero_title: str
    hero_summary: str
    hero_primary_cta_label: str
    hero_primary_cta_href: str
    hero_secondary_cta_label: str
    hero_secondary_cta_href: str
    trust_ribbon: str
    featured_content_heading: str
    buyer_paths: list[HomeBuyerPathSchema]
    core_categories: list[CategoryCardSchema]
    featured_cards: list[HomeFeaturedCardSchema]
    proof_items: list[HomeProofItemSchema]
    faq_items: list[FAQSchema]
