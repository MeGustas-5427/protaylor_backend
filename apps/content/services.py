from __future__ import annotations

from ninja.errors import HttpError

from apps.catalog.models import ProductCategory
from apps.content.models import HomeConfig
from apps.content.schemas import (
    HomeBuyerPathSchema,
    HomeConfigSchema,
    HomeFeaturedCardSchema,
    HomeProofItemSchema,
    HomeValuePointSchema,
)
from common.presenters import serialize_asset, serialize_category_card, serialize_faqs_for


def get_home_config() -> HomeConfigSchema:
    home = (
        HomeConfig.objects.filter(status=HomeConfig.Status.PUBLISHED, is_active=True)
        .prefetch_related("buyer_paths", "value_points", "featured_cards__asset", "proof_items__asset")
        .order_by("-updated_at")
        .first()
    )
    if not home:
        raise HttpError(404, "No published home configuration found.")

    categories = ProductCategory.objects.filter(
        status=ProductCategory.Status.PUBLISHED,
        is_core_category=True,
    ).order_by("name")

    return HomeConfigSchema(
        id=home.id,
        title=home.title,
        slug=home.slug,
        url_path=home.url_path,
        h1=home.h1,
        lead_text=home.lead_text or "",
        hero_eyebrow=home.hero_eyebrow or "",
        hero_title=home.hero_title,
        hero_summary=home.hero_summary,
        hero_primary_cta_label=home.hero_primary_cta_label or "",
        hero_primary_cta_href=home.hero_primary_cta_href or "",
        hero_secondary_cta_label=home.hero_secondary_cta_label or "",
        hero_secondary_cta_href=home.hero_secondary_cta_href or "",
        trust_ribbon=home.trust_ribbon or "",
        buyer_path_heading=home.buyer_path_heading or "",
        category_section_heading=home.category_section_heading or "",
        value_section_heading=home.value_section_heading or "",
        featured_content_heading=home.featured_content_heading or "",
        proof_section_heading=home.proof_section_heading or "",
        faq_section_heading=home.faq_section_heading or "",
        final_cta_title=home.final_cta_title or "",
        final_cta_body=home.final_cta_body or "",
        final_cta_primary_label=home.final_cta_primary_label or "",
        final_cta_primary_href=home.final_cta_primary_href or "",
        final_cta_secondary_label=home.final_cta_secondary_label or "",
        final_cta_secondary_href=home.final_cta_secondary_href or "",
        buyer_paths=[
            HomeBuyerPathSchema(
                id=item.id,
                audience_key=item.audience_key,
                title=item.title,
                summary=item.summary,
                cta_label=item.cta_label,
                cta_href=item.cta_href,
            )
            for item in home.buyer_paths.all().order_by("sort_order", "id")
        ],
        core_categories=[serialize_category_card(category) for category in categories],
        value_points=[
            HomeValuePointSchema(
                id=item.id,
                eyebrow=item.eyebrow or "",
                title=item.title,
                body=item.body,
            )
            for item in home.value_points.all().order_by("sort_order", "id")
        ],
        featured_cards=[
            HomeFeaturedCardSchema(
                id=item.id,
                card_type_code=item.card_type_code,
                title=item.title,
                summary=item.summary,
                href=item.href,
                asset=serialize_asset(item.asset),
            )
            for item in home.featured_cards.all().order_by("sort_order", "id")
        ],
        proof_items=[
            HomeProofItemSchema(
                id=item.id,
                proof_kind=item.proof_kind_code,
                title=item.title,
                evidence=item.evidence,
                source_name=item.source_name or "",
                source_role=item.source_role or "",
                source_company=item.source_company or "",
                href=item.href or "",
                asset=serialize_asset(item.asset),
            )
            for item in home.proof_items.all().order_by("sort_order", "id")
        ],
        faq_items=serialize_faqs_for(home),
    )
