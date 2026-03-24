from __future__ import annotations

from django.core.management import call_command
from django.test import TestCase

from apps.inquiries.models import Inquiry
from tests_support import build_api_client


class InquiryApiTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        call_command("seed_sample_site")

    def setUp(self) -> None:
        self.client = build_api_client()

    def test_inquiry_endpoint_persists_context(self) -> None:
        response = self.client.post(
            "/api/v1/inquiries/",
            data={
                "full_name": "Alice Buyer",
                "email": "alice@example.com",
                "company": "Buyer Co",
                "country": "USA",
                "business_type": "distributor",
                "target_use_case": "soft serve program",
                "message": "Need export pricing",
                "source_page_type": "product",
                "source_page_path": "/products/soft-ice-cream-machine/icm-t838-twin-twist-soft-serve-machine/",
                "source_page_title": "ICM-T838 Twin Twist Soft Serve Machine",
                "category_slug": "soft-ice-cream-machine",
                "product_slug": "icm-t838-twin-twist-soft-serve-machine",
                "variant_code": "ICM-T838-220V",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        inquiry = Inquiry.objects.get(email="alice@example.com")
        self.assertEqual(inquiry.source_context.product.slug, "icm-t838-twin-twist-soft-serve-machine")
