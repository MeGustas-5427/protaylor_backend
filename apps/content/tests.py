from __future__ import annotations

from django.core.management import call_command
from django.test import TestCase

from tests_support import build_api_client


class ContentApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        call_command("seed_sample_site")

    def setUp(self) -> None:
        self.client = build_api_client()

    def test_home_endpoint_returns_structured_home_config(self) -> None:
        response = self.client.get("/api/v1/site/home")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["slug"], "home")
        self.assertGreaterEqual(len(payload["buyer_paths"]), 1)
        self.assertGreaterEqual(len(payload["faq_items"]), 1)
