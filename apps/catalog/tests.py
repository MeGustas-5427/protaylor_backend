from __future__ import annotations

import tempfile
from pathlib import Path

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from openpyxl import Workbook

from apps.catalog.models import (
    Product,
    ProductCategory,
    ProductCategoryOperationalItem,
    ProductMedia,
    ProductRelation,
    ProductSpecGroup,
    ProductSpecRow,
)
from apps.catalog.services import get_product_detail
from apps.content.models import FAQItem, ResourceArticle
from apps.core.models import MediaAsset
from apps.core.models import PageSEO
from tests_support import build_api_client


class CatalogApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        call_command("seed_sample_site")

        cls.primary_product = Product.objects.select_related("category").get(
            slug="icm-t838-twin-twist-soft-serve-machine"
        )
        category = Product.objects.select_related("category").get(
            slug="icm-t838-twin-twist-soft-serve-machine"
        ).category
        product_image = MediaAsset.objects.get(title="ICM-T838 product hero")
        cls.related_resource = ResourceArticle.objects.get(slug="soft-serve-buying-guide")

        # Add a second canonical product so pagination overflow can be verified
        # against a multi-page result set without depending on production data.
        cls.extra_product = Product.objects.create(
            category=category,
            slug="icm-c220-compact-counter-soft-serve-machine",
            url_path="/products/soft-ice-cream-machine/icm-c220-compact-counter-soft-serve-machine/",
            name="ICM-C220 Compact Counter Soft Serve Machine",
            model_code="ICM-C220",
            h1="ICM-C220 Compact Counter Soft Serve Machine",
            summary="Compact soft serve model for cafes and low-footprint counters.",
            lead_text="A compact soft serve option for operators balancing footprint, menu range, and daily cleaning cadence.",
            seo_title="ICM-C220 Compact Counter Soft Serve Machine | PRO-TAYLOR",
            meta_description="Review the ICM-C220 compact counter soft serve machine for cafes and low-footprint dessert counters.",
            primary_query="compact counter soft serve machine",
            status=Product.Status.PUBLISHED,
            index_mode=Product.IndexMode.INDEX,
            is_canonical=True,
        )
        ProductMedia.objects.create(
            product=cls.extra_product,
            asset=product_image,
            media_kind=ProductMedia.MediaKind.HERO,
            is_primary=True,
            sort_order=10,
        )
        ProductRelation.objects.update_or_create(
            product=cls.primary_product,
            relation_type=ProductRelation.RelationType.RELATED_PRODUCT,
            related_product=cls.extra_product,
            defaults={"sort_order": 20},
        )

        def create_category(
            *,
            name: str,
            slug: str,
            url_path: str,
            parent: ProductCategory | None = None,
            operational_fit_title: str = "",
            buyer_review_focus_title: str = "",
        ) -> ProductCategory:
            return ProductCategory.objects.create(
                name=name,
                slug=slug,
                url_path=url_path,
                h1=name,
                summary=f"{name} summary",
                lead_text=f"{name} lead text",
                buyer_fit=f"{name} buyer fit",
                selection_guide=f"{name} selection guide",
                operational_fit_title=operational_fit_title,
                buyer_review_focus_title=buyer_review_focus_title,
                seo_title=f"{name} | PRO-TAYLOR",
                meta_description=f"{name} meta description",
                primary_query=name.lower(),
                status=ProductCategory.Status.PUBLISHED,
                index_mode=ProductCategory.IndexMode.INDEX,
                parent=parent,
            )

        def create_listing_ready_product(
            *,
            category: ProductCategory,
            slug: str,
            name: str,
            url_path: str,
        ) -> Product:
            product = Product.objects.create(
                category=category,
                slug=slug,
                url_path=url_path,
                name=name,
                model_code=slug.upper(),
                h1=name,
                summary=f"{name} summary",
                lead_text=f"{name} lead text",
                seo_title=f"{name} | PRO-TAYLOR",
                meta_description=f"{name} meta description",
                primary_query=name.lower(),
                status=Product.Status.PUBLISHED,
                index_mode=Product.IndexMode.INDEX,
                is_canonical=True,
            )
            ProductMedia.objects.create(
                product=product,
                asset=product_image,
                media_kind=ProductMedia.MediaKind.HERO,
                is_primary=True,
                sort_order=10,
            )
            quick_group = ProductSpecGroup.objects.create(
                product=product,
                title="Quick Facts",
                group_kind=ProductSpecGroup.GroupKind.QUICK_FACTS,
                sort_order=10,
            )
            ProductSpecRow.objects.create(
                group=quick_group,
                label="Output",
                value="30",
                unit="L/h",
                is_highlight=True,
                sort_order=10,
            )
            return product

        cls.parent_category = create_category(
            name="Ice Cream Machine",
            slug="ice-cream-machine",
            url_path="/products/ice-cream-machine/",
            operational_fit_title="Operational Fit",
            buyer_review_focus_title="Buyer Review Focus",
        )
        cls.gelato_child = create_category(
            name="Gelato Batch Freezer",
            slug="gelato-batch-freezer",
            url_path="/products/gelato-batch-freezer/",
            parent=cls.parent_category,
            operational_fit_title="Gelato Operational Fit",
            buyer_review_focus_title="Gelato Buyer Review Focus",
        )
        cls.roll_child = create_category(
            name="Roll Ice Cream Machine",
            slug="roll-ice-cream-machine",
            url_path="/products/roll-ice-cream-machine/",
            parent=cls.parent_category,
        )
        cls.parent_direct_product = create_listing_ready_product(
            category=cls.parent_category,
            slug="ice-cream-machine-direct-model",
            name="Ice Cream Machine Direct Model",
            url_path="/products/ice-cream-machine/ice-cream-machine-direct-model/",
        )
        cls.gelato_product = create_listing_ready_product(
            category=cls.gelato_child,
            slug="gelato-test-model",
            name="Gelato Test Model",
            url_path="/products/gelato-batch-freezer/gelato-test-model/",
        )
        cls.roll_product = create_listing_ready_product(
            category=cls.roll_child,
            slug="roll-test-model",
            name="Roll Test Model",
            url_path="/products/roll-ice-cream-machine/roll-test-model/",
        )
        ProductCategoryOperationalItem.objects.bulk_create(
            [
                ProductCategoryOperationalItem(
                    category=cls.parent_category,
                    section=ProductCategoryOperationalItem.Section.OPERATIONAL_FIT,
                    title="Application Matching",
                    body="Review equipment families against service format and expected daily throughput.",
                    icon="storefront",
                    sort_order=10,
                ),
                ProductCategoryOperationalItem(
                    category=cls.parent_category,
                    section=ProductCategoryOperationalItem.Section.OPERATIONAL_FIT,
                    title="Utility Planning",
                    body="Confirm voltage, cooling method, and placement constraints before final shortlist review.",
                    icon="bolt",
                    sort_order=20,
                ),
                ProductCategoryOperationalItem(
                    category=cls.parent_category,
                    section=ProductCategoryOperationalItem.Section.BUYER_REVIEW_FOCUS,
                    title="Capacity vs. Actual Demand",
                    body="Match peak-hour demand, recovery expectations, and product mix before sizing up.",
                    icon="query_stats",
                    sort_order=10,
                ),
                ProductCategoryOperationalItem(
                    category=cls.parent_category,
                    section=ProductCategoryOperationalItem.Section.BUYER_REVIEW_FOCUS,
                    title="Utilities and Footprint",
                    body="Check electrical supply, cooling environment, drainage, and working space before order lock.",
                    icon="home_work",
                    sort_order=20,
                ),
                ProductCategoryOperationalItem(
                    category=cls.gelato_child,
                    section=ProductCategoryOperationalItem.Section.OPERATIONAL_FIT,
                    title="Batch Capacity Fit",
                    body="Review batch size, extraction timing, and prep rhythm before comparing freezer classes.",
                    icon="speed",
                    sort_order=10,
                ),
                ProductCategoryOperationalItem(
                    category=cls.gelato_child,
                    section=ProductCategoryOperationalItem.Section.OPERATIONAL_FIT,
                    title="Kitchen Workflow",
                    body="Check charging, rinse, and pan transfer space before locking in a batch freezer footprint.",
                    icon="storefront",
                    sort_order=20,
                ),
                ProductCategoryOperationalItem(
                    category=cls.gelato_child,
                    section=ProductCategoryOperationalItem.Section.BUYER_REVIEW_FOCUS,
                    title="Freeze Curve Review",
                    body="Compare draw time, overrun control, and compressor recovery against daily production targets.",
                    icon="fact_check",
                    sort_order=10,
                ),
                ProductCategoryOperationalItem(
                    category=cls.gelato_child,
                    section=ProductCategoryOperationalItem.Section.BUYER_REVIEW_FOCUS,
                    title="Utilities by Batch",
                    body="Confirm power, clearance, and condenser conditions before selecting a higher-output batch platform.",
                    icon="bolt",
                    sort_order=20,
                ),
            ]
        )

        cls.single_child_parent = create_category(
            name="Home Use Slush Machine",
            slug="home-use-slush-machine",
            url_path="/products/home-use-slush-machine/",
        )
        cls.single_child = create_category(
            name="2L Slush Machine",
            slug="2l-slush-machine",
            url_path="/products/2l-slush-machine/",
            parent=cls.single_child_parent,
        )
        cls.single_child_product = create_listing_ready_product(
            category=cls.single_child,
            slug="2l-test-model",
            name="2L Test Model",
            url_path="/products/2l-slush-machine/2l-test-model/",
        )

        resource_image = MediaAsset.objects.create(
            title="Soft serve buying guide og",
            asset_kind=MediaAsset.AssetKind.IMAGE,
            file_url="https://cdn.example.com/protaylor/soft-serve-buying-guide-og.jpg",
            alt_text="Soft serve buying guide resource card",
            mime_type="image/jpeg",
        )
        PageSEO.objects.update_or_create(
            content_type=ContentType.objects.get_for_model(cls.related_resource, for_concrete_model=False),
            object_id=cls.related_resource.id,
            defaults={"og_image": resource_image},
        )

        FAQItem.objects.create(
            content_type=ContentType.objects.get_for_model(cls.primary_product, for_concrete_model=False),
            object_id=cls.primary_product.id,
            question="Does the ICM-T838 support OEM branding?",
            answer="Yes. Branding, control panel language, and export preparation can be aligned before order confirmation.",
            is_featured=False,
            sort_order=30,
        )

    def setUp(self) -> None:
        self.client = build_api_client()

    def test_category_endpoint_returns_products(self) -> None:
        response = self.client.get("/api/v1/catalog/categories/soft-ice-cream-machine")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["slug"], "soft-ice-cream-machine")
        self.assertGreaterEqual(len(payload["products"]), 1)

    def test_category_products_endpoint_returns_paginated_listing_contract(self) -> None:
        # 这里固定 page_size=1，是为了让分页窗口更稳定。
        # 即使将来这个分类下再补更多样例产品，这组断言也不会轻易漂移。
        response = self.client.get("/api/v1/catalog/categories/soft-ice-cream-machine/products?page=1&page_size=1")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["slug"], "soft-ice-cream-machine")
        self.assertEqual(payload["pagination"]["requested_page"], 1)
        self.assertEqual(payload["pagination"]["current_page"], 1)
        self.assertEqual(payload["pagination"]["page_size"], 1)
        self.assertEqual(payload["pagination"]["total_items"], 2)
        self.assertEqual(payload["pagination"]["total_pages"], 2)
        self.assertEqual(len(payload["items"]), 1)
        self.assertIn("card_image_url", payload["items"][0])
        self.assertIn("metrics", payload["items"][0])
        self.assertEqual(payload["operational_fit_title"], "Operational Fit")
        self.assertEqual(payload["buyer_review_focus_title"], "Buyer Review Focus")
        self.assertEqual(payload["operational_fit_items"], [])
        self.assertEqual(payload["buyer_review_focus_items"], [])

    def test_category_products_endpoint_overflow_page_returns_last_page(self) -> None:
        # 对这个公开 B2B 分类目录来说，超界页码应该回最后一页，
        # 不能把“分类存在但页码过期”误判成“资源不存在”。
        response = self.client.get(
            "/api/v1/catalog/categories/soft-ice-cream-machine/products?page=999&page_size=1"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["pagination"]["requested_page"], 999)
        self.assertEqual(payload["pagination"]["current_page"], 2)
        self.assertFalse(payload["pagination"]["has_next"])
        self.assertTrue(payload["pagination"]["has_previous"])
        self.assertEqual(payload["items"][0]["slug"], "icm-t838-twin-twist-soft-serve-machine")

    def test_product_paths_endpoint_returns_published_canonical_pairs(self) -> None:
        # 这个接口只服务前端 `generateStaticParams()`，
        # 所以测试只验证 category/product slug 对，不去耦合更重的详情字段。
        response = self.client.get("/api/v1/catalog/products/paths")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn(
            {
                "category_slug": "soft-ice-cream-machine",
                "product_slug": "icm-t838-twin-twist-soft-serve-machine",
            },
            payload,
        )
        self.assertIn(
            {
                "category_slug": "soft-ice-cream-machine",
                "product_slug": self.extra_product.slug,
            },
            payload,
        )

    def test_category_paths_endpoint_returns_published_category_pairs(self) -> None:
        # 这个接口只服务前端分类静态路径发现，因此断言只钉住最小字段契约。
        response = self.client.get("/api/v1/catalog/categories/paths")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn(
            {
                "slug": "soft-ice-cream-machine",
                "url_path": "/products/soft-ice-cream-machine/",
            },
            payload,
        )
        self.assertIn(
            {
                "slug": "ice-cream-machine",
                "url_path": "/products/ice-cream-machine/",
            },
            payload,
        )
        self.assertNotIn(
            {
                "slug": "gelato-batch-freezer",
                "url_path": "/products/gelato-batch-freezer/",
            },
            payload,
        )

    def test_categories_endpoint_returns_top_level_navigation_cards(self) -> None:
        response = self.client.get("/api/v1/catalog/categories")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ice_cream_category = next(item for item in payload if item["slug"] == "ice-cream-machine")
        self.assertEqual(ice_cream_category["product_count"], 3)
        self.assertTrue(ice_cream_category["has_children"])
        self.assertNotIn("gelato-batch-freezer", [item["slug"] for item in payload])

    def test_parent_category_products_endpoint_aggregates_children_and_returns_tabs(self) -> None:
        response = self.client.get("/api/v1/catalog/categories/ice-cream-machine/products")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["slug"], "ice-cream-machine")
        self.assertIsNone(payload["active_subcategory_slug"])
        self.assertEqual(len(payload["subcategory_tabs"]), 2)
        self.assertEqual({tab["slug"] for tab in payload["subcategory_tabs"]}, {"gelato-batch-freezer", "roll-ice-cream-machine"})
        self.assertEqual(payload["pagination"]["total_items"], 3)
        self.assertEqual(
            {item["subcategory_slug"] for item in payload["items"]},
            {"ice-cream-machine", "gelato-batch-freezer", "roll-ice-cream-machine"},
        )
        self.assertIn("subcategory_name", payload["items"][0])
        self.assertEqual(payload["operational_fit_title"], "Operational Fit")
        self.assertEqual(payload["buyer_review_focus_title"], "Buyer Review Focus")
        self.assertEqual(
            [item["title"] for item in payload["operational_fit_items"]],
            ["Application Matching", "Utility Planning"],
        )
        self.assertEqual(
            [item["section_code"] for item in payload["operational_fit_items"]],
            ["operational_fit", "operational_fit"],
        )
        self.assertEqual(
            [item["title"] for item in payload["buyer_review_focus_items"]],
            ["Capacity vs. Actual Demand", "Utilities and Footprint"],
        )
        self.assertEqual(
            [item["sort_order"] for item in payload["buyer_review_focus_items"]],
            [10, 20],
        )

    def test_parent_category_products_endpoint_filters_by_subcategory(self) -> None:
        response = self.client.get(
            "/api/v1/catalog/categories/ice-cream-machine/products?subcategory_slug=gelato-batch-freezer"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["active_subcategory_slug"], "gelato-batch-freezer")
        self.assertEqual(payload["pagination"]["total_items"], 1)
        self.assertEqual(payload["items"][0]["slug"], self.gelato_product.slug)
        self.assertEqual(payload["items"][0]["subcategory_slug"], "gelato-batch-freezer")
        self.assertEqual(payload["operational_fit_title"], "Gelato Operational Fit")
        self.assertEqual(payload["buyer_review_focus_title"], "Gelato Buyer Review Focus")
        self.assertEqual(
            [item["title"] for item in payload["operational_fit_items"]],
            ["Batch Capacity Fit", "Kitchen Workflow"],
        )
        self.assertEqual(
            [item["title"] for item in payload["buyer_review_focus_items"]],
            ["Freeze Curve Review", "Utilities by Batch"],
        )

    def test_parent_category_products_endpoint_falls_back_to_parent_operational_content_when_child_has_none(self) -> None:
        response = self.client.get(
            "/api/v1/catalog/categories/ice-cream-machine/products?subcategory_slug=roll-ice-cream-machine"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["active_subcategory_slug"], "roll-ice-cream-machine")
        self.assertEqual(payload["operational_fit_title"], "Operational Fit")
        self.assertEqual(payload["buyer_review_focus_title"], "Buyer Review Focus")
        self.assertEqual(
            [item["title"] for item in payload["operational_fit_items"]],
            ["Application Matching", "Utility Planning"],
        )
        self.assertEqual(
            [item["title"] for item in payload["buyer_review_focus_items"]],
            ["Capacity vs. Actual Demand", "Utilities and Footprint"],
        )

    def test_single_child_parent_products_endpoint_hides_tabs_but_aggregates_child(self) -> None:
        response = self.client.get("/api/v1/catalog/categories/home-use-slush-machine/products")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["slug"], "home-use-slush-machine")
        self.assertEqual(payload["active_subcategory_slug"], "2l-slush-machine")
        self.assertEqual(payload["subcategory_tabs"], [])
        self.assertEqual(payload["pagination"]["total_items"], 1)
        self.assertEqual(payload["items"][0]["slug"], self.single_child_product.slug)

    def test_leaf_category_products_endpoint_rejects_subcategory_filter(self) -> None:
        response = self.client.get(
            "/api/v1/catalog/categories/soft-ice-cream-machine/products?subcategory_slug=gelato-batch-freezer"
        )

        self.assertEqual(response.status_code, 400)

    def test_parent_category_products_endpoint_rejects_unknown_subcategory_filter(self) -> None:
        response = self.client.get(
            "/api/v1/catalog/categories/ice-cream-machine/products?subcategory_slug=not-a-real-child"
        )

        self.assertEqual(response.status_code, 400)

    def test_product_endpoint_returns_related_and_specs(self) -> None:
        response = self.client.get(
            "/api/v1/catalog/products/soft-ice-cream-machine/icm-t838-twin-twist-soft-serve-machine"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["model_code"], "ICM-T838")
        self.assertEqual(payload["hero_eyebrow"], "Soft Ice Cream Machines")
        self.assertGreaterEqual(len(payload["quick_facts"]), 1)
        self.assertGreaterEqual(len(payload["related_resources"]), 1)
        self.assertGreaterEqual(len(payload["related_products"]), 1)
        self.assertIn("group_kind_code", payload["spec_groups"][0])
        self.assertIn("image_url", payload["related_products"][0])
        self.assertIn("eyebrow", payload["related_products"][0])
        self.assertEqual(payload["related_resources"][0]["eyebrow"], "RESOURCE CENTER")
        self.assertTrue(payload["related_resources"][0]["image_url"])
        self.assertEqual(len(payload["faq_items"]), 3)
        self.assertTrue(
            any(faq["question"] == "Does the ICM-T838 support OEM branding?" for faq in payload["faq_items"])
        )

    def test_product_detail_service_only_exposes_first_three_product_faqs(self) -> None:
        FAQItem.objects.create(
            content_type=ContentType.objects.get_for_model(self.primary_product, for_concrete_model=False),
            object_id=self.primary_product.id,
            question="Should I over-size this model for every site?",
            answer="No. Oversizing usually creates a worse fit if daily demand, utilities, and floor plan do not require it.",
            is_featured=True,
            sort_order=40,
        )

        payload = get_product_detail(
            "soft-ice-cream-machine",
            "icm-t838-twin-twist-soft-serve-machine",
        )

        self.assertEqual(len(payload.faq_items), 3)
        self.assertNotIn(
            "Should I over-size this model for every site?",
            [faq.question for faq in payload.faq_items],
        )

    def test_import_product_faqs_command_replaces_product_bound_faqs(self) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "ProductTechnicalFaqs"
        sheet.append(
            [
                "Category",
                "Subcategory",
                "Product Name",
                "Product URL",
                "Source Product URL",
                "Model Code",
                "Series Label",
                "Primary Query",
                "Resource Topic ID",
                "Resource Title",
                "FAQ Family",
                "FAQ Slot",
                "Question",
                "Answer",
                "Sort Order",
                "Question Word Count",
                "Answer Word Count",
                "Key Signals",
                "QA Status",
                "Notes",
            ]
        )
        rows = [
            (1, 10, "Is this model suitable for a compact dessert counter?"),
            (2, 20, "How should I size this model for peak-hour demand?"),
            (3, 30, "What should I confirm before requesting a quote for this model?"),
        ]
        for slot, sort_order, question in rows:
            sheet.append(
                [
                    self.primary_product.category.name,
                    self.primary_product.category.name,
                    self.primary_product.name,
                    self.primary_product.url_path,
                    self.primary_product.source_url,
                    self.primary_product.model_code,
                    self.primary_product.series_label,
                    self.primary_product.primary_query,
                    "RA-001",
                    "How to Choose a Commercial Soft Serve Ice Cream Machine",
                    "Soft Serve / Frozen Yogurt",
                    slot,
                    question,
                    "Use the published configuration as a first filter, then confirm output, voltage, and available space.",
                    sort_order,
                    10,
                    16,
                    "output: 36-40 L/H",
                    "generated",
                    "",
                ]
            )

        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        handle.close()
        workbook.save(handle.name)
        workbook.close()

        try:
            call_command("import_product_faqs", excel=handle.name)
        finally:
            Path(handle.name).unlink(missing_ok=True)

        product_ct = ContentType.objects.get_for_model(self.primary_product, for_concrete_model=False)
        imported_faqs = list(
            FAQItem.objects.filter(content_type=product_ct, object_id=self.primary_product.id).order_by("sort_order", "id")
        )
        self.assertEqual(len(imported_faqs), 3)
        self.assertEqual(
            [faq.question for faq in imported_faqs],
            [
                "Is this model suitable for a compact dessert counter?",
                "How should I size this model for peak-hour demand?",
                "What should I confirm before requesting a quote for this model?",
            ],
        )

    def test_product_detail_service_stays_within_expected_query_budget(self) -> None:
        ContentType.objects.get_for_model(Product, for_concrete_model=False)

        with CaptureQueriesContext(connection) as ctx:
            payload = get_product_detail(
                "soft-ice-cream-machine",
                "icm-t838-twin-twist-soft-serve-machine",
            )

        self.assertEqual(payload.slug, "icm-t838-twin-twist-soft-serve-machine")
        self.assertLessEqual(len(ctx.captured_queries), 12)


class ImportCategoryOperationalItemsCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.parent_category = ProductCategory.objects.create(
            name="Ice Cream Machine",
            slug="ice-cream-machine",
            url_path="/products/ice-cream-machine/",
            h1="Ice Cream Machine",
            seo_title="Ice Cream Machine | PRO-TAYLOR",
            meta_description="Ice Cream Machine meta description",
            status=ProductCategory.Status.PUBLISHED,
            index_mode=ProductCategory.IndexMode.INDEX,
        )
        cls.child_category = ProductCategory.objects.create(
            name="Gelato Batch Freezer",
            slug="gelato-batch-freezer",
            url_path="/products/gelato-batch-freezer/",
            h1="Gelato Batch Freezer",
            seo_title="Gelato Batch Freezer | PRO-TAYLOR",
            meta_description="Gelato Batch Freezer meta description",
            status=ProductCategory.Status.PUBLISHED,
            index_mode=ProductCategory.IndexMode.INDEX,
            parent=cls.parent_category,
        )

    def _build_operational_seed_workbook(
        self,
        *,
        groups: list[dict[str, object]],
    ) -> str:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Operational Items Seed"
        sheet.append(
            [
                "source_category",
                "source_subcategory",
                "target_category_name",
                "target_scope",
                "operational_fit_title",
                "buyer_review_focus_title",
                "section_code",
                "sort_order",
                "item_title",
                "item_body",
                "icon",
                "is_active",
                "source_fields_used",
                "primary_source_url",
                "evidence_note",
                "confidence",
            ]
        )
        for group in groups:
            for row in group["rows"]:
                sheet.append(
                    [
                        group["source_category"],
                        group["source_subcategory"],
                        group["target_category_name"],
                        group["target_scope"],
                        group["operational_fit_title"],
                        group["buyer_review_focus_title"],
                        row["section_code"],
                        row["sort_order"],
                        row["item_title"],
                        row["item_body"],
                        row["icon"],
                        row["is_active"],
                        "summary;selection_guide",
                        "https://example.com/source",
                        "Evidence note",
                        0.95,
                    ]
                )

        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        handle.close()
        workbook.save(handle.name)
        workbook.close()
        return handle.name

    def test_import_category_operational_items_imports_parent_all_seed(self) -> None:
        workbook_path = self._build_operational_seed_workbook(
            groups=[
                {
                    "source_category": "Ice Cream Machine",
                    "source_subcategory": "── All ──",
                    "target_category_name": "Ice Cream Machine",
                    "target_scope": "parent_all",
                    "operational_fit_title": "Operational Fit",
                    "buyer_review_focus_title": "Buyer Review Focus",
                    "rows": [
                        {
                            "section_code": "operational_fit",
                            "sort_order": 1,
                            "item_title": "Application Matching",
                            "item_body": "Check service style and expected daily throughput before narrowing machine families.",
                            "icon": "storefront",
                            "is_active": True,
                        },
                        {
                            "section_code": "operational_fit",
                            "sort_order": 2,
                            "item_title": "Utility Planning",
                            "item_body": "Confirm voltage, cooling method, and placement limits before approving the shortlist.",
                            "icon": "bolt",
                            "is_active": True,
                        },
                        {
                            "section_code": "operational_fit",
                            "sort_order": 3,
                            "item_title": "Quote Readiness",
                            "item_body": "Bring target output and site constraints into the inquiry so model confirmation moves faster.",
                            "icon": "fact_check",
                            "is_active": True,
                        },
                        {
                            "section_code": "buyer_review_focus",
                            "sort_order": 1,
                            "item_title": "Capacity vs Demand",
                            "item_body": "Match peak demand, recovery expectations, and menu mix before sizing up.",
                            "icon": "speed",
                            "is_active": True,
                        },
                        {
                            "section_code": "buyer_review_focus",
                            "sort_order": 2,
                            "item_title": "Utilities and Space",
                            "item_body": "Check electrical supply, airflow, and working space before locking the model.",
                            "icon": "home_work",
                            "is_active": True,
                        },
                        {
                            "section_code": "buyer_review_focus",
                            "sort_order": 3,
                            "item_title": "Procurement Inputs",
                            "item_body": "Align quantity, target market, and compliance requirements before asking for final pricing.",
                            "icon": "fact_check",
                            "is_active": True,
                        },
                    ],
                }
            ]
        )

        try:
            call_command("import_category_operational_items", excel=workbook_path)
        finally:
            Path(workbook_path).unlink(missing_ok=True)

        self.parent_category.refresh_from_db()
        self.assertEqual(self.parent_category.operational_fit_title, "Operational Fit")
        self.assertEqual(self.parent_category.buyer_review_focus_title, "Buyer Review Focus")

        parent_items = list(
            ProductCategoryOperationalItem.objects.filter(category=self.parent_category).order_by("section", "sort_order")
        )
        self.assertEqual(len(parent_items), 6)
        self.assertEqual(
            [(item.section_code, item.sort_order, item.title) for item in parent_items],
            [
                ("operational_fit", 1, "Application Matching"),
                ("operational_fit", 2, "Utility Planning"),
                ("operational_fit", 3, "Quote Readiness"),
                ("buyer_review_focus", 1, "Capacity vs Demand"),
                ("buyer_review_focus", 2, "Utilities and Space"),
                ("buyer_review_focus", 3, "Procurement Inputs"),
            ],
        )

    def test_import_category_operational_items_replaces_existing_rows_on_rerun(self) -> None:
        ProductCategoryOperationalItem.objects.create(
            category=self.parent_category,
            section=ProductCategoryOperationalItem.Section.OPERATIONAL_FIT,
            title="Legacy Row",
            body="Legacy body",
            icon="storefront",
            sort_order=1,
        )
        self.parent_category.operational_fit_title = "Legacy Operational"
        self.parent_category.buyer_review_focus_title = "Legacy Buyer Focus"
        self.parent_category.save(update_fields=("operational_fit_title", "buyer_review_focus_title"))

        workbook_path = self._build_operational_seed_workbook(
            groups=[
                {
                    "source_category": "Ice Cream Machine",
                    "source_subcategory": "── All ──",
                    "target_category_name": "Ice Cream Machine",
                    "target_scope": "parent_all",
                    "operational_fit_title": "New Operational Fit",
                    "buyer_review_focus_title": "New Buyer Review Focus",
                    "rows": [
                        {
                            "section_code": "operational_fit",
                            "sort_order": 1,
                            "item_title": "Menu Match",
                            "item_body": "Choose machine families around product format and serving rhythm.",
                            "icon": "storefront",
                            "is_active": True,
                        },
                        {
                            "section_code": "operational_fit",
                            "sort_order": 2,
                            "item_title": "Site Utilities",
                            "item_body": "Check voltage, cooling, and placement before approving a final shortlist.",
                            "icon": "bolt",
                            "is_active": True,
                        },
                        {
                            "section_code": "operational_fit",
                            "sort_order": 3,
                            "item_title": "Inquiry Inputs",
                            "item_body": "Prepare output target and site notes before asking suppliers to confirm fit.",
                            "icon": "fact_check",
                            "is_active": True,
                        },
                        {
                            "section_code": "buyer_review_focus",
                            "sort_order": 1,
                            "item_title": "Peak Throughput",
                            "item_body": "Size for peak demand instead of only average daily volume.",
                            "icon": "speed",
                            "is_active": True,
                        },
                        {
                            "section_code": "buyer_review_focus",
                            "sort_order": 2,
                            "item_title": "Footprint Review",
                            "item_body": "Confirm working room and ventilation before model lock.",
                            "icon": "home_work",
                            "is_active": True,
                        },
                        {
                            "section_code": "buyer_review_focus",
                            "sort_order": 3,
                            "item_title": "Procurement Ready",
                            "item_body": "Align market, quantity, and compliance details before final quotation.",
                            "icon": "fact_check",
                            "is_active": False,
                        },
                    ],
                }
            ]
        )

        try:
            call_command("import_category_operational_items", excel=workbook_path)
        finally:
            Path(workbook_path).unlink(missing_ok=True)

        self.parent_category.refresh_from_db()
        self.assertEqual(self.parent_category.operational_fit_title, "New Operational Fit")
        self.assertEqual(self.parent_category.buyer_review_focus_title, "New Buyer Review Focus")
        parent_items = list(
            ProductCategoryOperationalItem.objects.filter(category=self.parent_category).order_by("section", "sort_order")
        )
        self.assertEqual(len(parent_items), 6)
        self.assertNotIn("Legacy Row", [item.title for item in parent_items])
        self.assertFalse(parent_items[-1].is_active)

    def test_import_category_operational_items_imports_subcategory_seed_to_child_category(self) -> None:
        workbook_path = self._build_operational_seed_workbook(
            groups=[
                {
                    "source_category": "Ice Cream Machine",
                    "source_subcategory": "Gelato Batch Freezer",
                    "target_category_name": "Gelato Batch Freezer",
                    "target_scope": "subcategory",
                    "operational_fit_title": "Operational Fit",
                    "buyer_review_focus_title": "Buyer Review Focus",
                    "rows": [
                        {
                            "section_code": "operational_fit",
                            "sort_order": 1,
                            "item_title": "Batch Size Match",
                            "item_body": "Choose bowl size around real batch cadence, not only headline output.",
                            "icon": "storefront",
                            "is_active": True,
                        },
                        {
                            "section_code": "operational_fit",
                            "sort_order": 2,
                            "item_title": "Cooling Setup",
                            "item_body": "Confirm power and condenser style before shortlisting gelato freezers.",
                            "icon": "bolt",
                            "is_active": True,
                        },
                        {
                            "section_code": "operational_fit",
                            "sort_order": 3,
                            "item_title": "Operator Skill",
                            "item_body": "Match controls and workflow to the team that will run daily batches.",
                            "icon": "fact_check",
                            "is_active": True,
                        },
                        {
                            "section_code": "buyer_review_focus",
                            "sort_order": 1,
                            "item_title": "Output Reality",
                            "item_body": "Check production per batch and pull-down time before promising menu volume.",
                            "icon": "speed",
                            "is_active": True,
                        },
                        {
                            "section_code": "buyer_review_focus",
                            "sort_order": 2,
                            "item_title": "Kitchen Footprint",
                            "item_body": "Review working clearance and cleaning access around the freezer body.",
                            "icon": "home_work",
                            "is_active": True,
                        },
                        {
                            "section_code": "buyer_review_focus",
                            "sort_order": 3,
                            "item_title": "Service Readiness",
                            "item_body": "Confirm spare parts and support response before committing a production line.",
                            "icon": "fact_check",
                            "is_active": True,
                        },
                    ],
                }
            ]
        )

        try:
            call_command("import_category_operational_items", excel=workbook_path)
        finally:
            Path(workbook_path).unlink(missing_ok=True)

        child_items = list(
            ProductCategoryOperationalItem.objects.filter(category=self.child_category).order_by("section", "sort_order")
        )
        self.assertEqual(len(child_items), 6)
        self.assertEqual(child_items[0].title, "Batch Size Match")
        self.assertEqual(child_items[-1].title, "Service Readiness")
        self.parent_category.refresh_from_db()
        self.child_category.refresh_from_db()
        self.assertEqual(self.child_category.operational_fit_title, "Operational Fit")
        self.assertEqual(self.parent_category.operational_fit_title, "")
