from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.catalog.models import (
    Product,
    ProductCategory,
    ProductFeature,
    ProductDownload,
    ProductMedia,
    ProductRelation,
    ProductSpecGroup,
    ProductSpecRow,
    ProductUseCase,
    ProductVariant,
)
from apps.content.models import (
    CompanyPage,
    FAQItem,
    HomeBuyerPath,
    HomeConfig,
    HomeFeaturedCard,
    HomeProofItem,
    ResourceArticle,
    SolutionPage,
)
from apps.core.models import (
    ContactChannel,
    FooterLink,
    FooterLinkGroup,
    MediaAsset,
    NavigationItem,
    OrganizationProfile,
    PageRelation,
    PageSEO,
)


class Command(BaseCommand):
    help = "Seed a coherent sample dataset for local frontend/backend integration."

    def handle(self, *args, **options):
        del args, options

        org, _ = OrganizationProfile.objects.update_or_create(
            brand_name="PRO-TAYLOR",
            defaults={
                "company_name": "Jiangmen PRO-TAYLOR Refrigeration Equipment Co., Ltd.",
                "legal_name": "Jiangmen PRO-TAYLOR Refrigeration Equipment Co., Ltd.",
                "short_description": "Commercial frozen dessert equipment manufacturer for wholesale, OEM, and dessert business buyers.",
                "headquarters_city": "Jiangmen",
                "headquarters_region": "Guangdong",
                "country": "China",
                "founded_year": 2016,
                "primary_email": "sales@protaylor.com",
                "primary_phone": "+86 750 0000 0000",
                "website_url": "https://www.protaylor.com/",
                "address": "No. 88 Industrial Road, Jiangmen, Guangdong, China",
                "is_active": True,
            },
        )

        hero_image, _ = MediaAsset.objects.update_or_create(
            title="Factory hero",
            defaults={
                "asset_kind": MediaAsset.AssetKind.IMAGE,
                "file_url": "https://cdn.example.com/protaylor/factory-hero.jpg",
                "alt_text": "PRO-TAYLOR factory and commercial frozen dessert equipment",
                "mime_type": "image/jpeg",
            },
        )
        product_image, _ = MediaAsset.objects.update_or_create(
            title="ICM-T838 product hero",
            defaults={
                "asset_kind": MediaAsset.AssetKind.IMAGE,
                "file_url": "https://cdn.example.com/protaylor/icm-t838.jpg",
                "alt_text": "ICM-T838 twin twist soft serve machine",
                "mime_type": "image/jpeg",
            },
        )
        spec_sheet, _ = MediaAsset.objects.update_or_create(
            title="ICM-T838 spec sheet",
            defaults={
                "asset_kind": MediaAsset.AssetKind.DOCUMENT,
                "file_url": "https://cdn.example.com/protaylor/icm-t838-spec-sheet.pdf",
                "mime_type": "application/pdf",
            },
        )

        ContactChannel.objects.update_or_create(
            organization=org,
            channel_type=ContactChannel.ChannelType.EMAIL,
            placement=ContactChannel.Placement.GLOBAL,
            label="Sales Email",
            defaults={
                "value": "sales@protaylor.com",
                "href": "mailto:sales@protaylor.com",
                "is_primary": True,
                "is_active": True,
                "sort_order": 10,
            },
        )
        ContactChannel.objects.update_or_create(
            organization=org,
            channel_type=ContactChannel.ChannelType.WHATSAPP,
            placement=ContactChannel.Placement.CONTACT_PAGE,
            label="WhatsApp",
            defaults={
                "value": "+86 13800000000",
                "href": "https://wa.me/8613800000000",
                "is_primary": False,
                "is_active": True,
                "sort_order": 20,
            },
        )

        top_nav = [
            ("Home", "/", 10),
            ("Solutions", "/solutions/commercial-wholesale-oem/", 20),
            ("Products", "/products/soft-ice-cream-machine/", 30),
            ("Resources", "/resources/soft-serve-buying-guide/", 40),
            ("Company", "/company/about/", 50),
            ("Contact", "/company/contact/", 60),
        ]
        for label, url_path, sort_order in top_nav:
            NavigationItem.objects.update_or_create(
                label=label,
                location=NavigationItem.Location.PRIMARY,
                defaults={
                    "url_path": url_path,
                    "sort_order": sort_order,
                    "is_active": True,
                },
            )

        footer_group, _ = FooterLinkGroup.objects.update_or_create(
            title="Products",
            defaults={"description": "Priority machine categories", "sort_order": 10, "is_active": True},
        )
        for label, url_path, sort_order in [
            ("Soft Ice Cream Machines", "/products/soft-ice-cream-machine/", 10),
            ("Ice Lolly Machines", "/products/ice-lolly-machine/", 20),
            ("Slush Freezer Machines", "/products/slush-freezer-machine/", 30),
        ]:
            FooterLink.objects.update_or_create(
                group=footer_group,
                label=label,
                defaults={"url_path": url_path, "sort_order": sort_order, "is_active": True},
            )

        trust_group, _ = FooterLinkGroup.objects.update_or_create(
            title="Company",
            defaults={"description": "Manufacturing proof and contact", "sort_order": 20, "is_active": True},
        )
        for label, url_path, sort_order in [
            ("About", "/company/about/", 10),
            ("Factory & Quality", "/company/factory-and-quality-control/", 20),
            ("Contact", "/company/contact/", 30),
        ]:
            FooterLink.objects.update_or_create(
                group=trust_group,
                label=label,
                defaults={"url_path": url_path, "sort_order": sort_order, "is_active": True},
            )

        solution_oem, _ = SolutionPage.objects.update_or_create(
            slug="commercial-wholesale-oem",
            defaults={
                "url_path": "/solutions/commercial-wholesale-oem/",
                "title": "Commercial, Wholesale, and OEM Solutions",
                "h1": "Commercial, Wholesale, and OEM Equipment Supply",
                "summary": "Factory-led supply path for importers, distributors, and OEM buyers.",
                "lead_text": "Use this path when you need portfolio planning, OEM support, and export coordination.",
                "seo_title": "Commercial Ice Cream Machine OEM and Wholesale Solutions | PRO-TAYLOR",
                "meta_description": "Factory-led equipment sourcing path for commercial, wholesale, and OEM buyers.",
                "primary_query": "commercial ice cream machine manufacturer",
                "solution_type": SolutionPage.SolutionType.COMMERCIAL,
                "status": SolutionPage.Status.PUBLISHED,
                "index_mode": SolutionPage.IndexMode.INDEX,
                "body": "Factory-led solution content placeholder.",
            },
        )
        SolutionPage.objects.update_or_create(
            slug="shop-cafe-dessert-business",
            defaults={
                "url_path": "/solutions/shop-cafe-dessert-business/",
                "title": "Shop, Cafe, and Dessert Business Solutions",
                "h1": "Machine Selection for Shops, Cafes, and Dessert Businesses",
                "summary": "Selection path for operators balancing menu fit, cleaning, and peak-hour output.",
                "lead_text": "Use this path when you are choosing machines for daily service and menu planning.",
                "seo_title": "Dessert Shop and Cafe Equipment Selection | PRO-TAYLOR",
                "meta_description": "Find the right frozen dessert equipment for shops, cafes, and dessert businesses.",
                "primary_query": "soft serve machine for shop business",
                "solution_type": SolutionPage.SolutionType.SHOP,
                "status": SolutionPage.Status.PUBLISHED,
                "index_mode": SolutionPage.IndexMode.INDEX,
                "body": "Operator-focused solution content placeholder.",
            },
        )

        resource, _ = ResourceArticle.objects.update_or_create(
            slug="soft-serve-buying-guide",
            defaults={
                "url_path": "/resources/soft-serve-buying-guide/",
                "title": "Soft Serve Machine Buying Guide",
                "h1": "How to Choose a Commercial Soft Serve Machine",
                "summary": "Decision guide for throughput, mix system, cleaning routine, and business fit.",
                "lead_text": "Start here if you need a practical comparison before shortlisting models.",
                "seo_title": "Commercial Soft Serve Machine Buying Guide | PRO-TAYLOR",
                "meta_description": "Learn how to compare commercial soft serve machines by output, use case, cleaning, and support.",
                "primary_query": "commercial soft serve machine buying guide",
                "resource_type": ResourceArticle.ResourceType.GUIDE,
                "status": ResourceArticle.Status.PUBLISHED,
                "index_mode": ResourceArticle.IndexMode.INDEX,
                "body": "Resource article placeholder for buyer education.",
            },
        )

        company_about, _ = CompanyPage.objects.update_or_create(
            slug="about",
            defaults={
                "url_path": "/company/about/",
                "title": "About PRO-TAYLOR",
                "h1": "About PRO-TAYLOR",
                "summary": "Manufacturing overview for international frozen dessert equipment buyers.",
                "lead_text": "Use this page to verify company focus, factory location, and export orientation.",
                "seo_title": "About PRO-TAYLOR | Commercial Frozen Dessert Equipment Manufacturer",
                "meta_description": "Learn about PRO-TAYLOR, its factory location, product focus, and export support.",
                "primary_query": "PRO-TAYLOR manufacturer",
                "page_kind": CompanyPage.PageKind.ABOUT,
                "status": CompanyPage.Status.PUBLISHED,
                "index_mode": CompanyPage.IndexMode.INDEX,
                "body": "Company overview placeholder.",
            },
        )
        CompanyPage.objects.update_or_create(
            slug="contact",
            defaults={
                "url_path": "/company/contact/",
                "title": "Contact PRO-TAYLOR",
                "h1": "Contact PRO-TAYLOR",
                "summary": "Direct contact page for distributor, OEM, and project inquiries.",
                "lead_text": "Send your target market, voltage, output goals, and machine shortlist.",
                "seo_title": "Contact PRO-TAYLOR | Request Quote",
                "meta_description": "Contact PRO-TAYLOR for machine selection, OEM discussions, and export-ready quotations.",
                "primary_query": "contact commercial ice cream machine manufacturer",
                "page_kind": CompanyPage.PageKind.CONTACT,
                "status": CompanyPage.Status.PUBLISHED,
                "index_mode": CompanyPage.IndexMode.INDEX,
                "body": "Contact page placeholder.",
            },
        )

        soft_serve_category, _ = ProductCategory.objects.update_or_create(
            slug="soft-ice-cream-machine",
            defaults={
                "url_path": "/products/soft-ice-cream-machine/",
                "name": "Soft Ice Cream Machines",
                "h1": "Commercial Soft Ice Cream Machines",
                "summary": "Commercial soft serve machines for dessert operators, distributors, and OEM projects.",
                "lead_text": "Use this category when you need continuous soft serve output and clear model comparison.",
                "buyer_fit": "Best for operators who need consistent texture, clean dispensing, and peak-hour stability.",
                "selection_guide": "Compare output, hopper size, electrical setup, and service access before choosing a model.",
                "seo_title": "Commercial Soft Ice Cream Machines | PRO-TAYLOR",
                "meta_description": "Explore commercial soft ice cream machines for dessert shops, distributors, and OEM buyers.",
                "primary_query": "commercial soft ice cream machine",
                "status": ProductCategory.Status.PUBLISHED,
                "index_mode": ProductCategory.IndexMode.INDEX,
                "is_core_category": True,
            },
        )
        ProductCategory.objects.update_or_create(
            slug="ice-lolly-machine",
            defaults={
                "url_path": "/products/ice-lolly-machine/",
                "name": "Ice Lolly Machines",
                "h1": "Commercial Ice Lolly Machines",
                "summary": "Machines for mold-based frozen pops and OEM branded ice lolly production.",
                "lead_text": "Use this category when you are producing popsicles or mold-based frozen treats.",
                "buyer_fit": "Best for OEM buyers and branded frozen snack projects.",
                "selection_guide": "Plan mold count, daily throughput, and product format before comparing models.",
                "seo_title": "Commercial Ice Lolly Machines | PRO-TAYLOR",
                "meta_description": "Explore ice lolly machines for branded popsicle and frozen treat production.",
                "primary_query": "ice lolly machine supplier",
                "status": ProductCategory.Status.PUBLISHED,
                "index_mode": ProductCategory.IndexMode.INDEX,
                "is_core_category": True,
            },
        )
        ProductCategory.objects.update_or_create(
            slug="slush-freezer-machine",
            defaults={
                "url_path": "/products/slush-freezer-machine/",
                "name": "Slush Freezer Machines",
                "h1": "Commercial Slush Freezer Machines",
                "summary": "Slush freezer machines for beverage service, frozen drink menus, and kiosk programs.",
                "lead_text": "Use this category when you need multi-flavor frozen beverage service equipment.",
                "buyer_fit": "Best for beverage operators, kiosks, and dessert counters with frozen drink demand.",
                "selection_guide": "Compare bowl count, recovery speed, and cleaning workflow.",
                "seo_title": "Commercial Slush Freezer Machines | PRO-TAYLOR",
                "meta_description": "Explore slush freezer machines for beverage shops and frozen drink programs.",
                "primary_query": "slush freezer machine supplier",
                "status": ProductCategory.Status.PUBLISHED,
                "index_mode": ProductCategory.IndexMode.INDEX,
                "is_core_category": True,
            },
        )

        product, _ = Product.objects.update_or_create(
            category=soft_serve_category,
            slug="icm-t838-twin-twist-soft-serve-machine",
            defaults={
                "url_path": "/products/soft-ice-cream-machine/icm-t838-twin-twist-soft-serve-machine/",
                "name": "ICM-T838 Twin Twist Soft Serve Machine",
                "model_code": "ICM-T838",
                "h1": "ICM-T838 Twin Twist Soft Serve Machine",
                "summary": "Floor-standing twin twist soft serve model for dessert shops and multi-flavor service.",
                "lead_text": "A commercial soft serve machine for operators who need stable daily service and two-flavor plus twist output.",
                "buyer_fit": "Suitable for dessert bars, cafes, kiosks, and international distributors building a soft serve portfolio.",
                "application_summary": "Supports cones, cups, and menu combinations in medium to high traffic settings.",
                "buyer_checklist": "Confirm voltage, expected servings per hour, cleaning routine, and local service process.",
                "customization_support": "Branding, voltage matching, and market-specific documentation can be aligned before order confirmation.",
                "packing_shipping": "Export packing, carton or wood support, and shipment coordination are available by order plan.",
                "after_sales_support": "Spare parts continuity, troubleshooting guidance, and service coordination are included in the support flow.",
                "seo_title": "ICM-T838 Twin Twist Soft Serve Machine | PRO-TAYLOR",
                "meta_description": "Review the ICM-T838 twin twist soft serve machine for dessert shop, distributor, and OEM sourcing.",
                "primary_query": "ICM-T838 twin twist soft serve machine",
                "status": Product.Status.PUBLISHED,
                "index_mode": Product.IndexMode.INDEX,
                "is_canonical": True,
            },
        )

        ProductVariant.objects.update_or_create(
            product=product,
            code="ICM-T838-220V",
            defaults={
                "name": "220V Standard Export",
                "voltage": "220V / 50Hz",
                "market": "Global",
                "summary": "Standard export variant for international sourcing.",
                "is_default": True,
                "status": ProductVariant.Status.PUBLISHED,
                "sort_order": 10,
            },
        )

        quick_group, _ = ProductSpecGroup.objects.update_or_create(
            product=product,
            title="Quick Facts",
            defaults={"group_kind": ProductSpecGroup.GroupKind.QUICK_FACTS, "sort_order": 10},
        )
        for label, value, unit, is_highlight, sort_order in [
            ("Output", "30", "L/h", True, 10),
            ("Hopper Capacity", "6 + 6", "L", True, 20),
            ("Cylinders", "2 x 1.8", "L", True, 30),
            ("Power", "2.2", "kW", True, 40),
        ]:
            ProductSpecRow.objects.update_or_create(
                group=quick_group,
                label=label,
                defaults={
                    "value": value,
                    "unit": unit,
                    "is_highlight": is_highlight,
                    "sort_order": sort_order,
                },
            )

        tech_group, _ = ProductSpecGroup.objects.update_or_create(
            product=product,
            title="Technical Specifications",
            defaults={"group_kind": ProductSpecGroup.GroupKind.TECHNICAL, "sort_order": 20},
        )
        for label, value, unit, sort_order in [
            ("Dimensions", "540 x 770 x 1420", "mm", 10),
            ("Net Weight", "150", "kg", 20),
            ("Refrigerant", "R404A", "", 30),
        ]:
            ProductSpecRow.objects.update_or_create(
                group=tech_group,
                label=label,
                defaults={"value": value, "unit": unit, "is_highlight": False, "sort_order": sort_order},
            )

        for title, body, sort_order in [
            ("Twin twist dispensing", "Supports two flavors plus twist for menu flexibility.", 10),
            ("Commercial operating stability", "Built for routine daily service in business environments.", 20),
            ("Service-friendly layout", "Component access is planned to simplify cleaning and maintenance routines.", 30),
        ]:
            ProductFeature.objects.update_or_create(
                product=product,
                title=title,
                defaults={"body": body, "sort_order": sort_order},
            )

        for title, summary, sort_order in [
            ("Dessert shop daily service", "Supports standard menu service with two flavors and twist output.", 10),
            ("Distributor sample selection", "Useful as a representative model in a distributor catalog.", 20),
        ]:
            ProductUseCase.objects.update_or_create(
                product=product,
                title=title,
                defaults={"summary": summary, "sort_order": sort_order},
            )

        product.media_items.update_or_create(
            product=product,
            asset=product_image,
            defaults={"media_kind": ProductMedia.MediaKind.HERO, "is_primary": True, "sort_order": 10},
        )
        product.downloads.update_or_create(
            product=product,
            asset=spec_sheet,
            defaults={"title": "ICM-T838 Spec Sheet", "download_kind": ProductDownload.DownloadKind.SPEC_SHEET, "sort_order": 10},
        )
        ProductRelation.objects.update_or_create(
            product=product,
            relation_type=ProductRelation.RelationType.RELATED_RESOURCE,
            related_resource=resource,
            defaults={"sort_order": 10},
        )

        home, _ = HomeConfig.objects.update_or_create(
            slug="home",
            defaults={
                "url_path": "/",
                "title": "Homepage",
                "h1": "Commercial Ice Cream and Frozen Dessert Equipment Manufacturer",
                "summary": "Homepage configuration for the English-main site.",
                "lead_text": "Factory-led frozen dessert equipment sourcing for wholesale, OEM, and dessert business buyers.",
                "hero_eyebrow": "Factory-led supply",
                "hero_title": "Commercial Ice Cream and Frozen Dessert Equipment Manufacturer",
                "hero_summary": "PRO-TAYLOR supports distributors, OEM buyers, and dessert businesses with machine selection, export coordination, and after-sales continuity.",
                "hero_primary_cta_label": "Explore Soft Serve Machines",
                "hero_primary_cta_href": soft_serve_category.url_path,
                "hero_secondary_cta_label": "Contact PRO-TAYLOR",
                "hero_secondary_cta_href": "/company/contact/",
                "trust_ribbon": "Factory production | Export support | OEM coordination | After-sales continuity",
                "featured_content_heading": "Recommended Starting Resources",
                "hero_image": hero_image,
                "value_section_image": product_image,
                "seo_title": "Commercial Ice Cream Machine Manufacturer for Wholesale, OEM, and Dessert Business | PRO-TAYLOR",
                "meta_description": "PRO-TAYLOR manufactures commercial soft serve, ice lolly, slush, and frozen dessert equipment for distributors, OEM programs, and dessert businesses worldwide.",
                "primary_query": "commercial ice cream machine manufacturer",
                "status": HomeConfig.Status.PUBLISHED,
                "index_mode": HomeConfig.IndexMode.INDEX,
                "is_active": True,
            },
        )

        for audience_key, title, summary, cta_label, cta_href, sort_order in [
            (
                "commercial-wholesale-oem",
                "Commercial, Wholesale, and OEM",
                "Best for importers, distributors, project buyers, and private-label programs.",
                "Explore commercial and OEM solutions",
                solution_oem.url_path,
                10,
            ),
            (
                "shop-cafe-dessert-business",
                "Shop, Cafe, and Dessert Business",
                "Best for operators choosing machines by menu, throughput, and cleaning practicality.",
                "Explore shop and dessert business solutions",
                "/solutions/shop-cafe-dessert-business/",
                20,
            ),
        ]:
            HomeBuyerPath.objects.update_or_create(
                home=home,
                audience_key=audience_key,
                defaults={
                    "title": title,
                    "summary": summary,
                    "cta_label": cta_label,
                    "cta_href": cta_href,
                    "sort_order": sort_order,
                },
            )

        HomeFeaturedCard.objects.update_or_create(
            home=home,
            title=resource.title,
            defaults={
                "card_type": HomeFeaturedCard.CardType.RESOURCE,
                "summary": resource.summary,
                "href": resource.url_path,
                "asset": hero_image,
                "sort_order": 10,
            },
        )
        HomeProofItem.objects.update_or_create(
            home=home,
            title="Factory and export service workflow",
            defaults={
                "proof_kind": HomeProofItem.ProofKind.CASE,
                "evidence": "Manufacturing base in Jiangmen with export-oriented coordination and after-sales continuity.",
                "source_name": "PRO-TAYLOR",
                "source_role": "Manufacturer",
                "href": company_about.url_path,
                "asset": hero_image,
                "sort_order": 10,
            },
        )

        for target, questions in {
            home: [
                (
                    "What does PRO-TAYLOR manufacture?",
                    "PRO-TAYLOR manufactures commercial frozen dessert and beverage equipment including soft serve, ice lolly, and slush machines.",
                ),
                (
                    "Who is the site designed for?",
                    "The site serves wholesale/OEM buyers and dessert business operators who need clear machine selection and sourcing support.",
                ),
            ],
            product: [
                (
                    "Who is the ICM-T838 suitable for?",
                    "It suits dessert shops, cafes, and distributors who need twin twist output and stable daily service.",
                ),
                (
                    "Can PRO-TAYLOR support export orders for this model?",
                    "Yes. Export packing, model confirmation, and service coordination can be aligned before shipment.",
                ),
            ],
        }.items():
            content_type = ContentType.objects.get_for_model(target, for_concrete_model=False)
            for index, (question, answer) in enumerate(questions, start=1):
                FAQItem.objects.update_or_create(
                    content_type=content_type,
                    object_id=target.id,
                    question=question,
                    defaults={"answer": answer, "is_featured": True, "sort_order": index * 10},
                )

        PageSEO.objects.update_or_create(
            content_type=ContentType.objects.get_for_model(home, for_concrete_model=False),
            object_id=home.id,
            defaults={
                "schema_profile": "Organization+WebSite+FAQPage",
                "og_title": home.seo_title,
                "og_description": home.meta_description,
                "og_image": hero_image,
            },
        )
        PageSEO.objects.update_or_create(
            content_type=ContentType.objects.get_for_model(product, for_concrete_model=False),
            object_id=product.id,
            defaults={
                "schema_profile": "Product+BreadcrumbList+FAQPage",
                "og_title": product.seo_title,
                "og_description": product.meta_description,
                "og_image": product_image,
            },
        )
        PageRelation.objects.update_or_create(
            source_content_type=ContentType.objects.get_for_model(product, for_concrete_model=False),
            source_object_id=product.id,
            target_content_type=ContentType.objects.get_for_model(resource, for_concrete_model=False),
            target_object_id=resource.id,
            relation_type=PageRelation.RelationType.RESOURCE,
            defaults={"note": "Buyer education support", "sort_order": 10},
        )

        self.stdout.write(self.style.SUCCESS("Sample site data seeded successfully."))
