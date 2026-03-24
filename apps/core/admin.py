from django.contrib import admin

from .models import (
    ContactChannel,
    FooterLink,
    FooterLinkGroup,
    MediaAsset,
    NavigationItem,
    OrganizationProfile,
    PageRelation,
    PageSEO,
)


class ContactChannelInline(admin.TabularInline):
    model = ContactChannel
    extra = 0
    show_change_link = True


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = ("brand_name", "company_name", "country", "primary_email", "is_active")
    search_fields = ("brand_name", "company_name", "primary_email")
    list_filter = ("country", "is_active")
    inlines = (ContactChannelInline,)


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("title", "asset_kind", "mime_type", "file_url")
    list_filter = ("asset_kind",)
    search_fields = ("title", "file_url", "alt_text")


@admin.register(ContactChannel)
class ContactChannelAdmin(admin.ModelAdmin):
    list_display = ("label", "channel_type", "placement", "organization", "is_primary", "is_active")
    list_filter = ("channel_type", "placement", "is_active", "is_primary")
    search_fields = ("label", "value", "href")
    list_select_related = ("organization",)


@admin.register(NavigationItem)
class NavigationItemAdmin(admin.ModelAdmin):
    list_display = ("label", "location", "parent", "url_path", "sort_order", "is_active")
    list_filter = ("location", "is_active")
    search_fields = ("label", "url_path")
    list_select_related = ("parent",)
    autocomplete_fields = ("parent",)


class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 0
    show_change_link = True


@admin.register(FooterLinkGroup)
class FooterLinkGroupAdmin(admin.ModelAdmin):
    list_display = ("title", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    inlines = (FooterLinkInline,)


@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "group", "url_path", "sort_order", "is_active")
    list_filter = ("group", "is_active")
    search_fields = ("label", "url_path")
    list_select_related = ("group",)


@admin.register(PageSEO)
class PageSEOAdmin(admin.ModelAdmin):
    list_display = ("content_type", "object_id", "schema_profile", "updated_at")
    list_filter = ("content_type", "schema_profile")
    search_fields = ("object_id", "schema_profile", "og_title", "og_description")
    list_select_related = ("content_type", "og_image")
    autocomplete_fields = ("og_image",)


@admin.register(PageRelation)
class PageRelationAdmin(admin.ModelAdmin):
    list_display = ("relation_type", "source_content_type", "source_object_id", "target_content_type", "target_object_id")
    list_filter = ("relation_type", "source_content_type", "target_content_type")
    search_fields = ("note",)
    list_select_related = ("source_content_type", "target_content_type")
