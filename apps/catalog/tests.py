from __future__ import annotations

from django.core.management import call_command
from django.test import TestCase

from tests_support import build_api_client


class CatalogApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        call_command("seed_sample_site")

    def setUp(self) -> None:
        self.client = build_api_client()

    def test_category_endpoint_returns_products(self) -> None:
        response = self.client.get("/api/v1/catalog/categories/soft-ice-cream-machine")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["slug"], "soft-ice-cream-machine")
        self.assertGreaterEqual(len(payload["products"]), 1)

    def test_product_endpoint_returns_related_and_specs(self) -> None:
        response = self.client.get(
            "/api/v1/catalog/products/soft-ice-cream-machine/icm-t838-twin-twist-soft-serve-machine"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["model_code"], "ICM-T838")
        self.assertGreaterEqual(len(payload["quick_facts"]), 1)
        self.assertGreaterEqual(len(payload["related_resources"]), 1)
