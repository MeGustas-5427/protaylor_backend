from __future__ import annotations

import tempfile
from pathlib import Path

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from openpyxl import Workbook

from apps.catalog.models import Product, ProductCategory, ProductMedia, ProductRelation
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
