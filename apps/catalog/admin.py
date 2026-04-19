from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet
from django.core.exceptions import ValidationError

from apps.content.models import FAQItem
from .models import (
    Product,
    ProductCategory,
    ProductCategoryFaqItem,
    ProductCategoryOperationalItem,
    ProductDownload,
    ProductFeature,
    ProductMedia,
    ProductRelation,
    ProductSpecGroup,
    ProductSpecRow,
    ProductUseCase,
    ProductVariant,
)


PRODUCT_TECHNICAL_FAQ_SORT_ORDERS = {10, 20, 30}


class TimestampReadonlyAdminMixin:
    readonly_fields = ("created_at", "updated_at")


class ProductFaqInlineFormSet(BaseGenericInlineFormSet):
    def clean(self) -> None:
        super().clean()
        if any(self.errors):
            return

        active_rows = 0
        sort_orders: list[int] = []
        for form in self.forms:
            cleaned_data = getattr(form, "cleaned_data", None)
            if not cleaned_data or cleaned_data.get("DELETE"):
                continue

            question = (cleaned_data.get("question") or "").strip()
            answer = (cleaned_data.get("answer") or "").strip()
            if not question and not answer:
                continue
            if not question or not answer:
                raise ValidationError("Each Technical Inquiry FAQ row requires both question and answer.")

            active_rows += 1
            sort_orders.append(int(cleaned_data.get("sort_order") or 0))

        if len(set(sort_orders)) != len(sort_orders):
            raise ValidationError("Technical Inquiry FAQ sort_order values must be unique per product.")

        invalid_sort_orders = [value for value in sort_orders if value not in PRODUCT_TECHNICAL_FAQ_SORT_ORDERS]
        if invalid_sort_orders:
            raise ValidationError("Technical Inquiry FAQ sort_order values must be 10, 20, and 30.")

        if (
            isinstance(self.instance, Product)
            and self.instance.status == Product.Status.PUBLISHED
            and self.instance.is_canonical
            and active_rows != 3
        ):
            raise ValidationError("Published canonical products must keep exactly three Technical Inquiry FAQ rows.")


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


class ProductFaqInline(GenericTabularInline):
    model = FAQItem
    formset = ProductFaqInlineFormSet
    ct_field = "content_type"
    ct_fk_field = "object_id"
    extra = 0
    fields = ("question", "answer", "sort_order")
    ordering = ("sort_order", "id")
    show_change_link = True
    verbose_name = "Technical Inquiry FAQ"
    verbose_name_plural = "Technical Inquiry FAQ"


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


class ProductCategoryOperationalItemInline(admin.TabularInline):
    model = ProductCategoryOperationalItem
    extra = 0
    fields = ("section", "title", "body", "icon", "sort_order", "is_active")
    show_change_link = True


class ProductCategoryFaqItemInline(admin.TabularInline):
    model = ProductCategoryFaqItem
    extra = 0
    fields = ("placement", "question", "answer", "sort_order", "is_active")
    show_change_link = True


@admin.register(ProductCategory)
class ProductCategoryAdmin(TimestampReadonlyAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "is_core_category", "status", "index_mode")
    list_filter = ("status", "index_mode", "is_core_category")
    search_fields = ("name", "slug", "primary_query")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    list_select_related = ("parent",)
    autocomplete_fields = ("parent",)
    inlines = (ProductCategoryOperationalItemInline, ProductCategoryFaqItemInline)
    fieldsets = (
        (
            "Category Identity",
            {
                "fields": (
                    "name",
                    "parent",
                    "slug",
                    "status",
                    "is_core_category",
                )
            },
        ),
        (
            "Category Messaging",
            {
                "fields": (
                    "h1",
                    "lead_text",
                    "summary",
                    "buyer_fit",
                    "selection_guide",
                    "operational_fit_title",
                    "buyer_review_focus_title",
                    "sourcing_faq_title",
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


@admin.register(ProductCategoryOperationalItem)
class ProductCategoryOperationalItemAdmin(TimestampReadonlyAdminMixin, admin.ModelAdmin):
    list_display = ("title", "category", "section_code", "sort_order", "is_active")
    list_filter = ("section", "is_active")
    search_fields = ("title", "body", "category__name")
    list_select_related = ("category",)
    autocomplete_fields = ("category",)


@admin.register(ProductCategoryFaqItem)
class ProductCategoryFaqItemAdmin(TimestampReadonlyAdminMixin, admin.ModelAdmin):
    list_display = ("question", "category", "placement_code", "sort_order", "is_active")
    list_filter = ("placement", "is_active")
    search_fields = ("question", "answer", "category__name")
    list_select_related = ("category",)
    autocomplete_fields = ("category",)


@admin.register(Product)
class ProductAdmin(TimestampReadonlyAdminMixin, admin.ModelAdmin):
    list_display = ("name", "category", "model_code", "series_label", "status", "is_canonical")
    list_filter = ("status", "is_canonical", "series", "category")
    search_fields = ("name", "model_code", "slug", "primary_query")
    list_select_related = ("category",)
    inlines = (
        ProductVariantInline,
        ProductFeatureInline,
        ProductUseCaseInline,
        ProductFaqInline,
        ProductMediaInline,
        ProductDownloadInline,
        ProductRelationInline,
    )
    autocomplete_fields = ("category",)
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (
            "Product Identity",
            {
                "fields": (
                    "category",
                    "name",
                    "model_code",
                    "series",
                    "slug",
                    "status",
                    "is_canonical",
                )
            },
        ),
        (
            "Buyer-Facing Content",
            {
                "fields": (
                    "h1",
                    "lead_text",
                    "summary",
                    "buyer_fit",
                    "application_summary",
                    "buyer_checklist",
                )
            },
        ),
        (
            "Sales & Support Messaging",
            {
                "fields": (
                    "customization_support",
                    "packing_shipping",
                    "after_sales_support",
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
        (
            "Source Archive",
            {
                "classes": ("collapse",),
                "fields": (
                    "source_url",
                    "raw_description",
                    "raw_attributes",
                ),
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


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
