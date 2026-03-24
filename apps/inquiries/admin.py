from django.contrib import admin

from .models import Inquiry, InquirySourceContext


class InquirySourceContextInline(admin.StackedInline):
    model = InquirySourceContext
    extra = 0
    autocomplete_fields = ("product", "variant")
    show_change_link = True


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "company", "country", "business_type", "status", "created_at")
    list_filter = ("status", "country", "business_type")
    search_fields = ("full_name", "email", "company", "message")
    date_hierarchy = "created_at"
    inlines = (InquirySourceContextInline,)


@admin.register(InquirySourceContext)
class InquirySourceContextAdmin(admin.ModelAdmin):
    list_display = ("inquiry", "source_page_type", "source_page_path", "product", "variant")
    list_filter = ("source_page_type",)
    search_fields = ("source_page_path", "source_page_title", "utm_source", "utm_campaign")
    list_select_related = ("inquiry", "product", "variant")
    autocomplete_fields = ("inquiry", "product", "variant")
