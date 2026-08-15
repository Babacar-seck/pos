"""Delivery marketplace integration routes — catalog, status badge, glance facts.

Covers the grill-with-docs session decisions in CONTEXT.md (Delivery Integrations):
5-state status_badge, tenant_name in place of the raw provider_key, last order
received, mapping count/last-modified, and 7-day unmapped-item rejection count.
"""
from __future__ import annotations

from datetime import timedelta

from pg_client_mixin import PgClientTestCase

from app import models, security


def _bearer_headers(user: models.User) -> dict[str, str]:
    data = {
        "sub": user.email,
        "tenant_id": user.tenant_id,
        "provider_id": getattr(user, "provider_id", None),
        "token_version": user.token_version,
    }
    token = security.create_access_token(data, expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}


class TestDeliveryIntegrationRoutes(PgClientTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tenant = models.Tenant(name="Boutique Paris 11")
        self.session.add(self.tenant)
        self.session.commit()
        self.session.refresh(self.tenant)

        self.owner = models.User(
            email="di-owner@test.local",
            hashed_password=security.get_password_hash("secret"),
            full_name="Owner",
            tenant_id=self.tenant.id,
            role=models.UserRole.owner,
        )
        self.session.add(self.owner)
        self.session.commit()
        self.session.refresh(self.owner)
        self.headers = _bearer_headers(self.owner)

        self.product = models.Product(
            tenant_id=self.tenant.id,
            name="Delivery Pizza",
            price_cents=1500,
            category="Main",
        )
        self.session.add(self.product)
        self.session.commit()
        self.session.refresh(self.product)

    def test_catalog_includes_just_eat(self) -> None:
        resp = self.client.get("/tenant/delivery-integrations/catalog", headers=self.headers)
        assert resp.status_code == 200
        keys = {row["provider_key"] for row in resp.json()}
        assert {"uber_eats", "glovo", "deliveroo", "just_eat", "stub"} <= keys

    def test_status_badge_lifecycle(self) -> None:
        # No row yet: absent from the list (frontend renders "not configured").
        resp = self.client.get("/tenant/delivery-integrations", headers=self.headers)
        assert resp.status_code == 200
        assert resp.json() == []

        # Created disabled -> disconnected.
        resp = self.client.put(
            "/tenant/delivery-integrations",
            headers=self.headers,
            json={"provider_key": "stub", "enabled": False},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status_badge"] == "disconnected"
        assert body["tenant_name"] == "Boutique Paris 11"
        assert body["mapping_count"] == 0
        assert body["unmapped_rejections_7d"] == 0
        assert body["last_order_received_at"] is None
        integration_id = body["id"]

        # Enabled, never tested -> pending_test (not a misleading green/red).
        resp = self.client.put(
            "/tenant/delivery-integrations",
            headers=self.headers,
            json={"provider_key": "stub", "enabled": True},
        )
        assert resp.status_code == 200
        assert resp.json()["status_badge"] == "pending_test"

        # Test with no credentials configured -> fails -> error.
        resp = self.client.post(
            f"/tenant/delivery-integrations/{integration_id}/test", headers=self.headers
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is False

        resp = self.client.get("/tenant/delivery-integrations", headers=self.headers)
        assert resp.json()[0]["status_badge"] == "error"

        # Configure credentials, test again -> connected.
        resp = self.client.put(
            "/tenant/delivery-integrations",
            headers=self.headers,
            json={
                "provider_key": "stub",
                "enabled": True,
                "credentials": {"api_key": "sandbox-key"},
            },
        )
        assert resp.status_code == 200
        resp = self.client.post(
            f"/tenant/delivery-integrations/{integration_id}/test", headers=self.headers
        )
        assert resp.json()["ok"] is True

        resp = self.client.get("/tenant/delivery-integrations", headers=self.headers)
        assert resp.json()[0]["status_badge"] == "connected"

        # Disabled again -> disconnected, regardless of last test result.
        resp = self.client.put(
            "/tenant/delivery-integrations",
            headers=self.headers,
            json={"provider_key": "stub", "enabled": False},
        )
        assert resp.json()["status_badge"] == "disconnected"

    def test_mapping_count_and_last_modified(self) -> None:
        resp = self.client.put(
            "/tenant/delivery-integrations",
            headers=self.headers,
            json={"provider_key": "stub", "enabled": True, "credentials": {"api_key": "k"}},
        )
        integration_id = resp.json()["id"]
        assert resp.json()["mapping_last_modified_at"] is None

        resp = self.client.put(
            f"/tenant/delivery-integrations/{integration_id}/mappings",
            headers=self.headers,
            json={"mappings": [{"external_item_id": "SKU_A", "product_id": None}]},
        )
        assert resp.status_code == 200

        resp = self.client.get("/tenant/delivery-integrations", headers=self.headers)
        row = resp.json()[0]
        assert row["mapping_count"] == 1
        assert row["mapping_last_modified_at"] is not None

    def test_unmapped_rejections_7d_and_last_order_received(self) -> None:
        resp = self.client.put(
            "/tenant/delivery-integrations",
            headers=self.headers,
            json={"provider_key": "stub", "enabled": True, "credentials": {"api_key": "k"}},
        )
        body = resp.json()
        integration_id = body["id"]
        webhook_token = body["webhook_ingest_token"]

        # Order line references a SKU with no catalog mapping -> rejected import.
        resp = self.client.post(
            f"/public/webhooks/delivery/{webhook_token}",
            json={
                "external_order_ref": "ORD-1",
                "lines": [{"external_item_id": "UNMAPPED_SKU", "quantity": 1}],
            },
        )
        assert resp.status_code == 422

        resp = self.client.get("/tenant/delivery-integrations", headers=self.headers)
        row = resp.json()[0]
        assert row["unmapped_rejections_7d"] == 1
        # This event was import_error, not webhook_order -> no last order received yet.
        assert row["last_order_received_at"] is None

        # Map the SKU to a real product, resend -> order created -> last_order_received_at populates.
        self.client.put(
            f"/tenant/delivery-integrations/{integration_id}/mappings",
            headers=self.headers,
            json={"mappings": [{"external_item_id": "UNMAPPED_SKU", "product_id": self.product.id}]},
        )
        resp = self.client.post(
            f"/public/webhooks/delivery/{webhook_token}",
            json={
                "external_order_ref": "ORD-2",
                "lines": [{"external_item_id": "UNMAPPED_SKU", "quantity": 1}],
            },
        )
        assert resp.status_code == 200

        resp = self.client.get("/tenant/delivery-integrations", headers=self.headers)
        row = resp.json()[0]
        assert row["last_order_received_at"] is not None
