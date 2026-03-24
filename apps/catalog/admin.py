from django.contrib import admin

from .models import (
    Product,
    ProductCategory,
    ProductDownload,
    ProductFeature,
    ProductMedia,
    ProductRelation,
    ProductSpecGroup,
    ProductSpecRow,
    ProductUseCase,
    ProductVariant,
)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    show_change_link = True


class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 0
    show_change_link = True


class ProductUseCaseInline(admin.TabularInline):
    model = ProductUseCase
    extra = 0
    show_change_link = True


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 0
    autocomplete_fields = ("asset",)
    show_change_link = True


class ProductDownloadInline(admin.TabularInline):
    model = ProductDownload
    extra = 0
    autocomplete_fields = ("asset",)
    show_change_link = True


class ProductRelationInline(admin.TabularInline):
    model = ProductRelation
    fk_name = "product"
    extra = 0
    autocomplete_fields = ("related_product", "related_resource")
    show_change_link = True


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_core_category", "status", "index_mode")
    list_filter = ("status", "index_mode", "is_core_category")
    search_fields = ("name", "slug", "primary_query")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "model_code", "status", "is_canonical")
    list_filter = ("status", "is_canonical", "category")
    search_fields = ("name", "model_code", "slug", "primary_query")
    list_select_related = ("category",)
    inlines = (
        ProductVariantInline,
        ProductFeatureInline,
        ProductUseCaseInline,
        ProductMediaInline,
        ProductDownloadInline,
        ProductRelationInline,
    )
    autocomplete_fields = ("category",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("name", "product", "code", "market", "is_default", "status")
    list_filter = ("status", "is_default", "market")
    search_fields = ("name", "code", "product__name")
    list_select_related = ("product",)
    autocomplete_fields = ("product",)


@admin.register(ProductSpecGroup)
class ProductSpecGroupAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "group_kind", "sort_order")
    list_filter = ("group_kind",)
    search_fields = ("title", "product__name")
    list_select_related = ("product",)
    autocomplete_fields = ("product",)


@admin.register(ProductSpecRow)
class ProductSpecRowAdmin(admin.ModelAdmin):
    list_display = ("label", "group", "value", "unit", "is_highlight", "sort_order")
    list_filter = ("is_highlight", "group__group_kind")
    search_fields = ("label", "value", "group__product__name")
    list_select_related = ("group", "group__product")
    autocomplete_fields = ("group",)


@admin.register(ProductFeature)
class ProductFeatureAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "sort_order")
    search_fields = ("title", "product__name")
    list_select_related = ("product",)
    autocomplete_fields = ("product",)


@admin.register(ProductUseCase)
class ProductUseCaseAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "sort_order")
    search_fields = ("title", "product__name")
    list_select_related = ("product",)
    autocomplete_fields = ("product",)


@admin.register(ProductMedia)
class ProductMediaAdmin(admin.ModelAdmin):
    list_display = ("product", "asset", "media_kind", "is_primary", "sort_order")
    list_filter = ("media_kind", "is_primary")
    list_select_related = ("product", "asset")
    search_fields = ("product__name", "asset__title", "alt_override")
    autocomplete_fields = ("product", "asset")


@admin.register(ProductDownload)
class ProductDownloadAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "download_kind", "sort_order")
    list_filter = ("download_kind",)
    search_fields = ("title", "product__name")
    list_select_related = ("product", "asset")
    autocomplete_fields = ("product", "asset")


@admin.register(ProductRelation)
class ProductRelationAdmin(admin.ModelAdmin):
    list_display = ("product", "relation_type", "related_product", "related_resource", "sort_order")
    list_filter = ("relation_type",)
    list_select_related = ("product", "related_product", "related_resource")
    search_fields = ("product__name", "related_product__name", "related_resource__title")
    autocomplete_fields = ("product", "related_product", "related_resource")
