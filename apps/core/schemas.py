from __future__ import annotations

from ninja import Schema
from pydantic import Field


class ContactChannelSchema(Schema):
    id: int
    channel_type: str
    placement: str
    label: str
    value: str
    href: str
    note: str
    is_primary: bool


class NavigationItemSchema(Schema):
    id: int
    label: str
    url_path: str
    location: str
    open_in_new_tab: bool
    children: list["NavigationItemSchema"] = Field(default_factory=list)


NavigationItemSchema.model_rebuild()


class FooterLinkSchema(Schema):
    id: int
    label: str
    url_path: str
    open_in_new_tab: bool


class FooterLinkGroupSchema(Schema):
    id: int
    title: str
    description: str
    links: list[FooterLinkSchema]


class OrganizationProfileSchema(Schema):
    id: int
    company_name: str
    brand_name: str
    legal_name: str
    short_description: str
    headquarters_city: str
    headquarters_region: str
    country: str
    founded_year: int | None = None
    primary_email: str
    primary_phone: str
    website_url: str
    address: str
    postal_code: str


class SiteChromeSchema(Schema):
    organization: OrganizationProfileSchema
    navigation: list[NavigationItemSchema]
    footer_groups: list[FooterLinkGroupSchema]
    contact_channels: list[ContactChannelSchema]
