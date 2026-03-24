from __future__ import annotations

from django.conf import settings
from ninja.errors import HttpError

from apps.catalog.models import Product, ProductVariant
from apps.inquiries.models import Inquiry, InquirySourceContext
from apps.inquiries.schemas import (
    InquiryAcceptedSchema,
    InquiryCreateSchema,
    RevalidateRequestSchema,
    RevalidateResponseSchema,
)


def create_inquiry(payload: InquiryCreateSchema) -> InquiryAcceptedSchema:
    product = None
    variant = None

    if payload.product_slug:
        queryset = Product.objects.all()
        if payload.category_slug:
            queryset = queryset.filter(category__slug=payload.category_slug)
        product = queryset.filter(slug=payload.product_slug).first()

    if payload.variant_code and product:
        variant = ProductVariant.objects.filter(product=product, code=payload.variant_code).first()

    inquiry = Inquiry.objects.create(
        full_name=payload.full_name,
        email=payload.email,
        company=payload.company,
        phone=payload.phone,
        country=payload.country,
        business_type=payload.business_type,
        target_use_case=payload.target_use_case,
        message=payload.message,
        consent_to_contact=payload.consent_to_contact,
    )
    InquirySourceContext.objects.create(
        inquiry=inquiry,
        source_page_type=payload.source_page_type,
        source_page_path=payload.source_page_path,
        source_page_title=payload.source_page_title,
        product=product,
        variant=variant,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        referer=payload.referer,
    )
    return InquiryAcceptedSchema(
        inquiry_id=inquiry.id,
        status=inquiry.status_code,
        message="Inquiry accepted. A sales coordinator can now qualify and respond.",
    )


def accept_revalidate(payload: RevalidateRequestSchema) -> RevalidateResponseSchema:
    if settings.REVALIDATE_SHARED_SECRET and payload.secret != settings.REVALIDATE_SHARED_SECRET:
        raise HttpError(403, "Invalid revalidate secret.")

    return RevalidateResponseSchema(
        accepted=True,
        contract_version="v1",
        message=(
            "Revalidate webhook contract accepted. "
            "Wire this endpoint to Next.js on-demand revalidation in deployment."
        ),
        paths=payload.paths,
        tags=payload.tags,
    )
