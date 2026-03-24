from __future__ import annotations

from typing import Any

from ninja import Router

from apps.core.schemas import (
    ContactChannelSchema,
    FooterLinkGroupSchema,
    NavigationItemSchema,
    OrganizationProfileSchema,
    SiteChromeSchema,
)
from apps.core.services import (
    get_active_organization,
    get_contact_channels,
    get_footer_groups,
    get_navigation_tree,
    get_site_chrome,
    serialize_organization,
)

router = Router(tags=["site"])


@router.get("/organization", response=OrganizationProfileSchema)
def get_organization_profile(request: Any) -> OrganizationProfileSchema:
    del request
    return serialize_organization(get_active_organization())


@router.get("/navigation", response=list[NavigationItemSchema])
def get_navigation(request: Any) -> list[NavigationItemSchema]:
    del request
    return get_navigation_tree()


@router.get("/footer", response=list[FooterLinkGroupSchema])
def get_footer(request: Any) -> list[FooterLinkGroupSchema]:
    del request
    return get_footer_groups()


@router.get("/contact-channels", response=list[ContactChannelSchema])
def get_channels(request: Any) -> list[ContactChannelSchema]:
    del request
    return get_contact_channels()


@router.get("/chrome", response=SiteChromeSchema)
def get_chrome(request: Any) -> SiteChromeSchema:
    del request
    return get_site_chrome()
