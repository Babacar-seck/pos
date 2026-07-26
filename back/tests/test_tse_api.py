"""German TSE API: sale/storno signing, live gate, DSFinV-K stub (#316)."""
from __future__ import annotations

import unittest
from datetime import date, timedelta
from unittest import mock

from pg_client_mixin import PgClientTestCase

from app import models, security
from app.tse_service import STUB_SCHEMA, assert_tse_mode_allowed


def _bearer_headers(user: models.User) -> dict[str, str]:
    data = {
        "sub": user.email,
        "tenant_id": user.tenant_id,
        "provider_id": getattr(user, "provider_id", None),
        "token_version": user.token_version,
    }
    token = security.create_access_token(data, expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}


class TestTseApi(PgClientTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tenant = models.Tenant(
            name="TSE Tenant",
            tse_mode="test",
            fiscal_country="DE",
            fiscal_mode="off",
        )
        self.session.add(self.tenant)
        self.session.commit()
        self.session.refresh(self.tenant)

        self.owner = models.User(
            email="owner-tse@test.local",
            hashed_password=security.get_password_hash("x"),
            full_name="Owner",
            tenant_id=self.tenant.id,
            role=models.UserRole.owner,
        )
        self.session.add(self.owner)
        self.session.commit()
        self.session.refresh(self.owner)

        floor = models.Floor(name="Main", sort_order=0, tenant_id=self.tenant.id)
        self.session.add(floor)
        self.session.commit()
        self.session.refresh(floor)

        table = models.Table(
            name="T1",
            token="tok-tse-1",
            floor_id=floor.id,
            tenant_id=self.tenant.id,
            x_position=0,
            y_position=0,
            rotation=0,
            shape="rect",
            width=1,
            height=1,
            seat_count=2,
            is_active=True,
        )
        self.session.add(table)
        self.session.commit()
        self.session.refresh(table)
        self.table = table

        self.order_paid = models.Order(
            tenant_id=self.tenant.id,
            table_id=table.id,
            status=models.OrderStatus.paid,
        )
        self.order_pending = models.Order(
            tenant_id=self.tenant.id,
            table_id=table.id,
            status=models.OrderStatus.pending,
        )
        self.session.add(self.order_paid)
        self.session.add(self.order_pending)
        self.session.commit()
        self.session.refresh(self.order_paid)
        self.session.refresh(self.order_pending)

        product = models.Product(
            name="TSE Dish",
            price_cents=2500,
            tenant_id=self.tenant.id,
        )
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)

        item = models.OrderItem(
            order_id=self.order_paid.id,
            product_id=product.id,
            product_name=product.name,
            quantity=1,
            price_cents=2500,
            status=models.OrderItemStatus.delivered,
        )
        self.session.add(item)
        self.session.commit()
        self.product = product

    def test_sign_sale_idempotent_and_fields(self) -> None:
        h = _bearer_headers(self.owner)
        r1 = self.client.post(
            f"/orders/{self.order_paid.id}/tse-transaction/sign", headers=h
        )
        self.assertEqual(r1.status_code, 200, r1.text)
        body1 = r1.json()
        self.assertEqual(body1["process_type"], "sale")
        self.assertEqual(body1["mode"], "test")
        self.assertTrue(body1.get("tse_serial"))
        self.assertGreaterEqual(body1.get("signature_counter", 0), 1)
        self.assertTrue(body1.get("signature_value"))
        self.assertTrue(body1.get("qr_content"))
        self.assertIn("disclaimer", body1)

        r2 = self.client.post(
            f"/orders/{self.order_paid.id}/tse-transaction/sign", headers=h
        )
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertEqual(r2.json()["id"], body1["id"])

        g = self.client.get(
            f"/orders/{self.order_paid.id}/tse-transaction", headers=h
        )
        self.assertEqual(g.status_code, 200, g.text)
        self.assertEqual(g.json()["id"], body1["id"])

    def test_sign_unpaid_fails(self) -> None:
        h = _bearer_headers(self.owner)
        r = self.client.post(
            f"/orders/{self.order_pending.id}/tse-transaction/sign", headers=h
        )
        self.assertEqual(r.status_code, 400, r.text)

    def test_sign_when_tse_off_fails(self) -> None:
        self.tenant.tse_mode = "off"
        self.session.add(self.tenant)
        self.session.commit()
        h = _bearer_headers(self.owner)
        r = self.client.post(
            f"/orders/{self.order_paid.id}/tse-transaction/sign", headers=h
        )
        self.assertEqual(r.status_code, 400, r.text)

    def test_mark_paid_creates_tse_sale(self) -> None:
        order = models.Order(
            tenant_id=self.tenant.id,
            table_id=self.table.id,
            status=models.OrderStatus.pending,
        )
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        self.session.add(
            models.OrderItem(
                order_id=order.id,
                product_id=self.product.id,
                product_name=self.product.name,
                quantity=1,
                price_cents=2500,
                status=models.OrderItemStatus.delivered,
            )
        )
        self.session.commit()

        h = _bearer_headers(self.owner)
        r = self.client.put(
            f"/orders/{order.id}/mark-paid",
            headers=h,
            json={"payment_method": "cash"},
        )
        self.assertEqual(r.status_code, 200, r.text)
        g = self.client.get(f"/orders/{order.id}/tse-transaction", headers=h)
        self.assertEqual(g.status_code, 200, g.text)
        self.assertEqual(g.json()["process_type"], "sale")

    def test_unmark_paid_creates_storno(self) -> None:
        from datetime import datetime, timezone

        from sqlmodel import select

        h = _bearer_headers(self.owner)
        self.client.post(
            f"/orders/{self.order_paid.id}/tse-transaction/sign", headers=h
        )
        self.order_paid.paid_at = datetime.now(timezone.utc)
        self.session.add(self.order_paid)
        self.session.commit()

        r = self.client.put(f"/orders/{self.order_paid.id}/unmark-paid", headers=h)
        self.assertEqual(r.status_code, 200, r.text)

        rows = list(
            self.session.exec(
                select(models.TseTransaction).where(
                    models.TseTransaction.order_id == self.order_paid.id
                )
            ).all()
        )
        types = {row.process_type for row in rows}
        self.assertIn("sale", types)
        self.assertIn("storno", types)

    def test_dsfinvk_export_stub(self) -> None:
        h = _bearer_headers(self.owner)
        self.client.post(
            f"/orders/{self.order_paid.id}/tse-transaction/sign", headers=h
        )
        today = date.today().isoformat()
        r = self.client.get(
            f"/tenant/tse/dsfinvk-export?from={today}&to={today}", headers=h
        )
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(body.get("schema"), "pos.dsfinvk.stub.v1")
        self.assertGreaterEqual(body.get("count", 0), 1)
        self.assertIn("disclaimer", body)

    def test_live_mode_gated(self) -> None:
        with mock.patch("app.tse_service.settings") as s:
            s.tse_live_unlock = False
            s.tse_provider_base_url = ""
            with self.assertRaises(Exception):
                assert_tse_mode_allowed("live")

        h = _bearer_headers(self.owner)
        r = self.client.put(
            "/tenant/settings",
            headers=h,
            json={"tse_mode": "live"},
        )
        self.assertEqual(r.status_code, 400, r.text)

    def test_verifactu_untouched(self) -> None:
        """TSE must not require or alter fiscal_mode."""
        self.assertEqual(self.tenant.fiscal_mode, "off")
        h = _bearer_headers(self.owner)
        r = self.client.post(
            f"/orders/{self.order_paid.id}/tse-transaction/sign", headers=h
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.session.refresh(self.tenant)
        self.assertEqual(self.tenant.fiscal_mode, "off")
        self.assertEqual(STUB_SCHEMA, "pos.tse.stub.v1")


if __name__ == "__main__":
    unittest.main()
