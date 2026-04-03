from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.catalog.models import Product, ProductMedia
from apps.catalog.services import get_product_detail
from apps.core.models import MediaAsset
from tests_support import build_api_client


class CatalogApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        call_command("seed_sample_site")

        category = Product.objects.select_related("category").get(
            slug="icm-t838-twin-twist-soft-serve-machine"
        ).category
        product_image = MediaAsset.objects.get(title="ICM-T838 product hero")

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

    def test_product_endpoint_returns_related_and_specs(self) -> None:
        response = self.client.get(
            "/api/v1/catalog/products/soft-ice-cream-machine/icm-t838-twin-twist-soft-serve-machine"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["model_code"], "ICM-T838")
        self.assertGreaterEqual(len(payload["quick_facts"]), 1)
        self.assertGreaterEqual(len(payload["related_resources"]), 1)
        self.assertIn("group_kind_code", payload["spec_groups"][0])

    def test_product_detail_service_stays_within_expected_query_budget(self) -> None:
        ContentType.objects.get_for_model(Product, for_concrete_model=False)

        with CaptureQueriesContext(connection) as ctx:
            payload = get_product_detail(
                "soft-ice-cream-machine",
                "icm-t838-twin-twist-soft-serve-machine",
            )

        self.assertEqual(payload.slug, "icm-t838-twin-twist-soft-serve-machine")
        self.assertLessEqual(len(ctx.captured_queries), 12)
