from __future__ import annotations

from typing import Any

from ninja import Router

from apps.inquiries.schemas import (
    InquiryAcceptedSchema,
    InquiryCreateSchema,
    RevalidateRequestSchema,
    RevalidateResponseSchema,
)
from apps.inquiries.services import accept_revalidate, create_inquiry

router = Router(tags=["inquiries"])


@router.post("", response=InquiryAcceptedSchema)
def submit_inquiry(request: Any, payload: InquiryCreateSchema) -> InquiryAcceptedSchema:
    del request
    return create_inquiry(payload)


@router.post("/revalidate-hook", response=RevalidateResponseSchema)
def revalidate_hook(request: Any, payload: RevalidateRequestSchema) -> RevalidateResponseSchema:
    del request
    return accept_revalidate(payload)
