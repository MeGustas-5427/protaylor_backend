from django.contrib import admin

from .models import (
    CompanyPage,
    FAQItem,
    HomeBuyerPath,
    HomeConfig,
    HomeFeaturedCard,
    HomeProofItem,
    HomeValuePoint,
    ResourceArticle,
    SolutionPage,
)


class TimestampReadonlyAdminMixin:
    readonly_fields = ("created_at", "updated_at")


class BasePageAdmin(TimestampReadonlyAdminMixin, admin.ModelAdmin):
    search_fields = ("title", "slug", "primary_query")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"

    @staticmethod
    def get_base_fieldsets(page_kind_field: str | None = None):
        identity_fields = ["title"]
        if page_kind_field:
            identity_fields.append(page_kind_field)
        identity_fields.extend(["slug", "status"])
        return (
            ("Page Identity", {"fields": tuple(identity_fields)}),
            ("Page Content", {"fields": ("h1", "lead_text", "summary", "body")}),
            (
                "SEO & Indexing",
                {
                    "fields": (
                        "url_path",
                        "seo_title",
                        "meta_description",
                        "canonical_url",
                        "index_mode",
                        "primary_query",
                        "secondary_queries",
                        "published_at",
                    )
                },
            ),
            ("Timestamps", {"fields": ("created_at", "updated_at")}),
        )


class HomeBuyerPathInline(admin.TabularInline):
    model = HomeBuyerPath
    extra = 0
    show_change_link = True


class HomeValuePointInline(admin.TabularInline):
    model = HomeValuePoint
    extra = 0
    show_change_link = True


class HomeFeaturedCardInline(admin.TabularInline):
    model = HomeFeaturedCard
    extra = 0
    autocomplete_fields = ("asset",)
    show_change_link = True


class HomeProofItemInline(admin.TabularInline):
    model = HomeProofItem
    extra = 0
    autocomplete_fields = ("asset",)
    show_change_link = True


@admin.register(HomeConfig)
class HomeConfigAdmin(TimestampReadonlyAdminMixin, admin.ModelAdmin):
    list_display = ("title", "slug", "status", "is_active", "updated_at")
    list_filter = ("status", "is_active", "index_mode")
    search_fields = ("title", "slug", "hero_title")
    prepopulated_fields = {"slug": ("title",)}
    inlines = (
        HomeBuyerPathInline,
        HomeValuePointInline,
        HomeFeaturedCardInline,
        HomeProofItemInline,
    )
    fieldsets = (
        ("Page Identity", {"fields": ("title", "slug", "status", "is_active")}),
        (
            "Hero",
            {
                "fields": (
                    "h1",
                    "lead_text",
                    "hero_eyebrow",
                    "hero_title",
                    "hero_summary",
                    "trust_ribbon",
                )
            },
        ),
        (
            "Hero CTAs",
            {
                "fields": (
                    "hero_primary_cta_label",
                    "hero_primary_cta_href",
                    "hero_secondary_cta_label",
                    "hero_secondary_cta_href",
                )
            },
        ),
        (
            "Section Headings",
            {
                "fields": (
                    "buyer_path_heading",
                    "category_section_heading",
                    "value_section_heading",
                    "featured_content_heading",
                    "proof_section_heading",
                    "faq_section_heading",
                )
            },
        ),
        (
            "Final CTA",
            {
                "fields": (
                    "final_cta_title",
                    "final_cta_body",
                    "final_cta_primary_label",
                    "final_cta_primary_href",
                    "final_cta_secondary_label",
                    "final_cta_secondary_href",
                )
            },
        ),
        (
            "SEO & Indexing",
            {
                "fields": (
                    "url_path",
                    "seo_title",
                    "meta_description",
                    "canonical_url",
                    "index_mode",
                    "primary_query",
                    "secondary_queries",
                    "published_at",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(HomeBuyerPath)
class HomeBuyerPathAdmin(admin.ModelAdmin):
    list_display = ("title", "audience_key", "home", "sort_order")
    search_fields = ("title", "audience_key")
    list_select_related = ("home",)
    autocomplete_fields = ("home",)


@admin.register(HomeValuePoint)
class HomeValuePointAdmin(admin.ModelAdmin):
    list_display = ("title", "home", "sort_order")
    search_fields = ("title",)
    list_select_related = ("home",)
    autocomplete_fields = ("home",)


@admin.register(HomeFeaturedCard)
class HomeFeaturedCardAdmin(admin.ModelAdmin):
    list_display = ("title", "card_type", "home", "sort_order")
    list_filter = ("card_type",)
    search_fields = ("title", "href")
    list_select_related = ("home", "asset")
    autocomplete_fields = ("home", "asset")


@admin.register(HomeProofItem)
class HomeProofItemAdmin(admin.ModelAdmin):
    list_display = ("title", "proof_kind", "home", "sort_order")
    list_filter = ("proof_kind",)
    search_fields = ("title", "source_name", "source_company")
    list_select_related = ("home", "asset")
    autocomplete_fields = ("home", "asset")


@admin.register(SolutionPage)
class SolutionPageAdmin(BasePageAdmin):
    list_display = ("title", "solution_type", "status", "index_mode")
    list_filter = ("solution_type", "status", "index_mode")
    fieldsets = BasePageAdmin.get_base_fieldsets("solution_type")


@admin.register(ResourceArticle)
class ResourceArticleAdmin(BasePageAdmin):
    list_display = ("title", "resource_type", "status", "index_mode")
    list_filter = ("resource_type", "status", "index_mode")
    fieldsets = BasePageAdmin.get_base_fieldsets("resource_type")


@admin.register(CompanyPage)
class CompanyPageAdmin(BasePageAdmin):
    list_display = ("title", "page_kind", "status", "index_mode")
    list_filter = ("page_kind", "status", "index_mode")
    fieldsets = BasePageAdmin.get_base_fieldsets("page_kind")


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ("question", "content_type", "object_id", "is_featured", "sort_order")
    list_filter = ("content_type", "is_featured")
    search_fields = ("question", "answer")
    list_select_related = ("content_type",)
