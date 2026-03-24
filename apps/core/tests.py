from __future__ import annotations

from django.core.management import call_command
from django.test import TestCase

from tests_support import build_api_client


class CoreApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        call_command("seed_sample_site")

    def setUp(self) -> None:
        self.client = build_api_client()

    def test_site_chrome_endpoint_returns_navigation_and_org(self) -> None:
        response = self.client.get("/api/v1/site/chrome")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["organization"]["brand_name"], "PRO-TAYLOR")
        self.assertGreaterEqual(len(payload["navigation"]), 1)

    def test_healthcheck_endpoint_returns_ok(self) -> None:
        response = self.client.get("/healthz/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
