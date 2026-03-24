from __future__ import annotations

from django.db.models import Prefetch
from ninja.errors import HttpError

from apps.core.models import ContactChannel, FooterLink, FooterLinkGroup, NavigationItem, OrganizationProfile
from apps.core.schemas import (
    ContactChannelSchema,
    FooterLinkGroupSchema,
    FooterLinkSchema,
    NavigationItemSchema,
    OrganizationProfileSchema,
    SiteChromeSchema,
)


def serialize_navigation_node(item: NavigationItem) -> NavigationItemSchema:
    children = [
        serialize_navigation_node(child)
        for child in getattr(item, "_child_items", [])
    ]
    return NavigationItemSchema(
        id=item.id,
        label=item.label,
        url_path=item.url_path,
        location=item.location_code,
        open_in_new_tab=item.open_in_new_tab,
        children=children,
    )


def serialize_organization(organization: OrganizationProfile) -> OrganizationProfileSchema:
    return OrganizationProfileSchema(
        id=organization.id,
        company_name=organization.company_name,
        brand_name=organization.brand_name,
        legal_name=organization.legal_name or "",
        short_description=organization.short_description or "",
        headquarters_city=organization.headquarters_city or "",
        headquarters_region=organization.headquarters_region or "",
        country=organization.country or "",
        founded_year=organization.founded_year,
        primary_email=organization.primary_email or "",
        primary_phone=organization.primary_phone or "",
        website_url=organization.website_url or "",
        address=organization.address or "",
        postal_code=organization.postal_code or "",
    )


def get_active_organization() -> OrganizationProfile:
    organization = OrganizationProfile.objects.filter(is_active=True).order_by("-updated_at").first()
    if not organization:
        raise HttpError(404, "No active organization profile found.")
    return organization


def get_navigation_tree() -> list[NavigationItemSchema]:
    items = (
        NavigationItem.objects.filter(location=NavigationItem.Location.PRIMARY, is_active=True)
        .select_related("parent")
        .prefetch_related("children")
        .order_by("sort_order", "id")
    )
    item_map = {item.id: item for item in items}
    for item in item_map.values():
        item._child_items = []
    roots: list[NavigationItem] = []
    for item in items:
        if item.parent_id and item.parent_id in item_map:
            item_map[item.parent_id]._child_items.append(item)
        else:
            roots.append(item)
    return [serialize_navigation_node(item) for item in roots]


def get_footer_groups() -> list[FooterLinkGroupSchema]:
    groups = FooterLinkGroup.objects.filter(is_active=True).prefetch_related("links").order_by("sort_order", "id")
    return [
        FooterLinkGroupSchema(
            id=group.id,
            title=group.title,
            description=group.description or "",
            links=[
                FooterLinkSchema(
                    id=link.id,
                    label=link.label,
                    url_path=link.url_path,
                    open_in_new_tab=link.open_in_new_tab,
                )
                for link in group.links.filter(is_active=True).order_by("sort_order", "id")
            ],
        )
        for group in groups
    ]


def get_contact_channels() -> list[ContactChannelSchema]:
    channels = ContactChannel.objects.filter(is_active=True).select_related("organization").order_by("sort_order", "id")
    return [
        ContactChannelSchema(
            id=channel.id,
            channel_type=channel.channel_type_code,
            placement=channel.placement_code,
            label=channel.label,
            value=channel.value,
            href=channel.href or "",
            note=channel.note or "",
            is_primary=channel.is_primary,
        )
        for channel in channels
    ]


def get_site_chrome() -> SiteChromeSchema:
    organization = serialize_organization(get_active_organization())

    navigation_items = (
        NavigationItem.objects.filter(
            location=NavigationItem.Location.PRIMARY,
            is_active=True,
            parent__isnull=True,
        )
        .prefetch_related(
            Prefetch(
                "children",
                queryset=NavigationItem.objects.filter(is_active=True).order_by("sort_order", "id"),
                to_attr="_child_items",
            )
        )
        .order_by("sort_order", "id")
    )

    footer_groups = (
        FooterLinkGroup.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch(
                "links",
                queryset=FooterLink.objects.filter(is_active=True).order_by("sort_order", "id"),
            )
        )
        .order_by("sort_order", "id")
    )

    channels = ContactChannel.objects.filter(
        organization__is_active=True,
        is_active=True,
    ).order_by("sort_order", "id")

    return SiteChromeSchema(
        organization=organization,
        navigation=[serialize_navigation_node(item) for item in navigation_items],
        footer_groups=[
            FooterLinkGroupSchema(
                id=group.id,
                title=group.title,
                description=group.description or "",
                links=[
                    FooterLinkSchema(
                        id=link.id,
                        label=link.label,
                        url_path=link.url_path,
                        open_in_new_tab=link.open_in_new_tab,
                    )
                    for link in group.links.all()
                ],
            )
            for group in footer_groups
        ],
        contact_channels=[
            ContactChannelSchema(
                id=channel.id,
                channel_type=channel.channel_type_code,
                placement=channel.placement_code,
                label=channel.label,
                value=channel.value,
                href=channel.href or "",
                note=channel.note or "",
                is_primary=channel.is_primary,
            )
            for channel in channels
        ],
    )
