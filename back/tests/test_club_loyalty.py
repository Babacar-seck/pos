"""Club loyalty MVP tests (#327)."""

from __future__ import annotations

from datetime import timedelta

from pg_client_mixin import PgClientTestCase
from sqlmodel import select

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


class TestClubLoyalty(PgClientTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tenant = models.Tenant(name="Loyalty Cafe")
        self.other = models.Tenant(name="Other Place")
        self.session.add(self.tenant)
        self.session.add(self.other)
        self.session.commit()
        self.session.refresh(self.tenant)
        self.session.refresh(self.other)

        pwd = security.get_password_hash("x")
        self.admin = models.User(
            email="loyalty-admin@amvara.de",
            hashed_password=pwd,
            full_name="Admin",
            role=models.UserRole.admin,
            tenant_id=self.tenant.id,
        )
        self.waiter = models.User(
            email="loyalty-waiter@amvara.de",
            hashed_password=pwd,
            full_name="Waiter",
            role=models.UserRole.waiter,
            tenant_id=self.tenant.id,
        )
        self.other_admin = models.User(
            email="loyalty-other@amvara.de",
            hashed_password=pwd,
            full_name="Other",
            role=models.UserRole.admin,
            tenant_id=self.other.id,
        )
        self.session.add(self.admin)
        self.session.add(self.waiter)
        self.session.add(self.other_admin)
        self.session.commit()
        self.session.refresh(self.admin)
        self.session.refresh(self.waiter)
        self.session.refresh(self.other_admin)

        floor = models.Floor(tenant_id=self.tenant.id, name="Main", sort_order=0)
        self.session.add(floor)
        self.session.commit()
        self.session.refresh(floor)
        self.table = models.Table(
            tenant_id=self.tenant.id,
            floor_id=floor.id,
            name="T1",
            token="loyalty-t1-token",
            x_position=0,
            y_position=0,
            rotation=0,
            shape="rect",
            width=1,
            height=1,
            seat_count=4,
            is_active=True,
        )
        self.session.add(self.table)
        self.product = models.Product(
            tenant_id=self.tenant.id,
            name="Coffee",
            price_cents=400,
        )
        self.session.add(self.product)
        self.session.commit()
        self.session.refresh(self.table)
        self.session.refresh(self.product)

    def _enable_program(self, **overrides):
        h = _bearer_headers(self.admin)
        body = {
            "enabled": True,
            "program_name": "Cafe Club",
            "mode": "stamps",
            "earn_units_per_order": 1,
            "redemption_threshold": 3,
            "reward_discount_cents": 400,
        }
        body.update(overrides)
        r = self.client.put("/loyalty/program", json=body, headers=h)
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_tenant_isolation_program(self):
        self._enable_program()
        r = self.client.get("/loyalty/program", headers=_bearer_headers(self.other_admin))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data["enabled"])
        self.assertNotEqual(data.get("program_name"), "Cafe Club")

    def test_public_join_and_balance(self):
        self._enable_program()
        r = self.client.post(
            f"/public/tenants/{self.tenant.id}/loyalty/join",
            json={
                "display_name": "Alex Guest",
                "email": "alex.loyalty@amvara.de",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        token = r.json()["membership"]["member_token"]
        self.assertTrue(token)

        bal = self.client.get(f"/public/loyalty/members/{token}")
        self.assertEqual(bal.status_code, 200)
        self.assertEqual(bal.json()["membership"]["balance"], 0)
        self.assertEqual(bal.json()["program"]["program_name"], "Cafe Club")

    def test_earn_once_on_mark_paid(self):
        self._enable_program(earn_units_per_order=2)
        join = self.client.post(
            f"/public/tenants/{self.tenant.id}/loyalty/join",
            json={"display_name": "Pat", "phone": "+34600111222"},
        ).json()
        mid = join["membership"]["id"]

        order = models.Order(
            tenant_id=self.tenant.id,
            table_id=self.table.id,
            status=models.OrderStatus.pending,
            loyalty_membership_id=mid,
        )
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        item = models.OrderItem(
            order_id=order.id,
            product_id=self.product.id,
            product_name="Coffee",
            quantity=1,
            price_cents=400,
            status=models.OrderItemStatus.pending,
        )
        self.session.add(item)
        self.session.commit()

        h = _bearer_headers(self.waiter)
        r = self.client.put(
            f"/orders/{order.id}/mark-paid",
            json={"payment_method": "cash"},
            headers=h,
        )
        self.assertEqual(r.status_code, 200, r.text)

        membership = self.session.get(models.LoyaltyMembership, mid)
        self.session.refresh(membership)
        self.assertEqual(membership.balance, 2)

        r2 = self.client.put(
            f"/orders/{order.id}/mark-paid",
            json={"payment_method": "cash"},
            headers=h,
        )
        self.assertEqual(r2.status_code, 400)
        self.session.refresh(membership)
        self.assertEqual(membership.balance, 2)

        earns = self.session.exec(
            select(models.LoyaltyLedgerEntry).where(
                models.LoyaltyLedgerEntry.order_id == order.id,
                models.LoyaltyLedgerEntry.entry_type == "earn",
            )
        ).all()
        self.assertEqual(len(earns), 1)

    def test_redeem_and_non_negative_balance(self):
        self._enable_program(
            earn_units_per_order=1,
            redemption_threshold=2,
            reward_discount_cents=350,
        )
        join = self.client.post(
            f"/public/tenants/{self.tenant.id}/loyalty/join",
            json={"display_name": "Sam", "email": "sam.loyalty@amvara.de"},
        ).json()
        mid = join["membership"]["id"]
        token = join["membership"]["member_token"]

        adj = self.client.post(
            f"/loyalty/memberships/{mid}/adjust",
            json={"delta_units": 2, "note": "seed"},
            headers=_bearer_headers(self.admin),
        )
        self.assertEqual(adj.status_code, 200, adj.text)
        self.assertEqual(adj.json()["membership"]["balance"], 2)

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
                product_name="Coffee",
                quantity=2,
                price_cents=400,
                status=models.OrderItemStatus.pending,
            )
        )
        self.session.commit()

        redeem = self.client.post(
            f"/orders/{order.id}/loyalty/redeem",
            json={"member_token": token},
            headers=_bearer_headers(self.waiter),
        )
        self.assertEqual(redeem.status_code, 200, redeem.text)
        self.assertEqual(redeem.json()["discount_cents"], 350)
        self.assertEqual(redeem.json()["balance"], 0)

        self.session.refresh(order)
        self.assertEqual(order.loyalty_discount_cents, 350)
        self.assertEqual(order.loyalty_units_redeemed, 2)

        bad = self.client.post(
            f"/loyalty/memberships/{mid}/adjust",
            json={"delta_units": -1, "note": "overdraw"},
            headers=_bearer_headers(self.admin),
        )
        self.assertEqual(bad.status_code, 400)

        denied = self.client.put(
            "/loyalty/program",
            json={"enabled": False},
            headers=_bearer_headers(self.waiter),
        )
        self.assertEqual(denied.status_code, 403)

    def test_wallet_status_unconfigured(self):
        self._enable_program()
        join = self.client.post(
            f"/public/tenants/{self.tenant.id}/loyalty/join",
            json={"display_name": "Wal", "email": "wal.loyalty@amvara.de"},
        ).json()
        token = join["membership"]["member_token"]
        r = self.client.get(f"/public/loyalty/members/{token}/wallet")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["apple_wallet_available"])
        self.assertFalse(r.json()["google_wallet_available"])
