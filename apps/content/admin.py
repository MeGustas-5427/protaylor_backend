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
class HomeConfigAdmin(admin.ModelAdmin):
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
class SolutionPageAdmin(admin.ModelAdmin):
    list_display = ("title", "solution_type", "status", "index_mode")
    list_filter = ("solution_type", "status", "index_mode")
    search_fields = ("title", "slug", "primary_query")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"


@admin.register(ResourceArticle)
class ResourceArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "resource_type", "status", "index_mode")
    list_filter = ("resource_type", "status", "index_mode")
    search_fields = ("title", "slug", "primary_query")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"


@admin.register(CompanyPage)
class CompanyPageAdmin(admin.ModelAdmin):
    list_display = ("title", "page_kind", "status", "index_mode")
    list_filter = ("page_kind", "status", "index_mode")
    search_fields = ("title", "slug", "primary_query")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ("question", "content_type", "object_id", "is_featured", "sort_order")
    list_filter = ("content_type", "is_featured")
    search_fields = ("question", "answer")
    list_select_related = ("content_type",)
