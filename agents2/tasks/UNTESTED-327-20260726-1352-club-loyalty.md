# Club loyalty (points/stamps + wallet)

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/327
- **327**

## Problem / goal

No native loyalty/retention module exists. Tenants today need third-party punch-card/points SaaS (e.g. wallet-only tools) with no POS checkout integration. Goal: tenant-scoped loyalty (points or stamps), earn on paid order completion, redeem at checkout, and Apple/Google Wallet passes on join — distinct from pricing promos (**#322**). Builds on `BillingCustomer` / `docs/0017-billing-customers-factura.md` and existing tenant auth patterns.

## High-level instructions for coder

- Start with an **MVP slice**: data model (`LoyaltyProgram`, membership, append-only ledger tied to `order.id`) + auto-earn on order paid + staff redeem at checkout; defer tiered VIP / referral / birthday rewards.
- Keep redemption discounts aligned with whatever discount/audit path **#322** (price promos) introduces — do not invent a second parallel discount mechanism.
- Award **once per completed order**, not per split-payment leg (coordinate with split-bill work when present).
- Wallet: follow official PassKit / Google Wallet specs; document Apple signing cert + Google issuer/service-account as operational deps in a new `docs/00XX-loyalty-program.md`. Do not guess signing formats.
- Staff: settings UI for program rules; order flow shows balance / redeem. Permissions via existing owner/admin checks; decide who may adjust points manually.
- Customer: join via QR/link (menu or dedicated URL); simple balance view. Tenant isolation + pytest for earn/redeem and non-negative balance.
- `CHANGELOG.md` entry; append **Testing instructions**. No secrets or live PII in fixtures.

## Implementation notes (010 feature coder)

- Models + migration `20260726162500_club_loyalty.sql`; service `back/app/loyalty_service.py`.
- Earn hooked after mark-paid / finish / Stripe / Revolut confirm (idempotent ledger).
- Redemption uses `order.loyalty_discount_cents` until #322; documented in `docs/0066-club-loyalty.md`.
- Wallet: status API reports unavailable until Apple/Google env certs are set (no invented PassKit signing).
- Staff: Settings → Loyalty club; payment modal redeem by member token.
- Public: `/loyalty/{tenantId}`, `/loyalty/card/{memberToken}`.
- Pytest: `back/tests/test_club_loyalty.py` (5 passed).

## Testing instructions

1. **Migrate:** From repo root with stack up:  
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python -m app.migrate`  
   Expect schema version includes `20260726162500`.

2. **Pytest:**  
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python3 -m pytest tests/test_club_loyalty.py -q`  
   Expect **5 passed** (tenant isolation, join/balance, earn-once on mark-paid, redeem + non-negative, wallet unconfigured).

3. **Staff settings:** Log in as owner/admin → **Settings → Loyalty club** (`data-testid=settings-loyalty-tab`). Enable program, set earn/threshold/reward, Save. Confirm join URL shown (`data-testid=loyalty-join-url`).

4. **Public join:** Open `/loyalty/{tenantId}` (tenant with program enabled). Submit name + email or phone. Expect success (`data-testid=loyalty-join-success`) and a card link `/loyalty/card/{token}` that shows balance 0.

5. **Earn:** Staff unpaid order → set membership on order (`PUT /orders/{id}/loyalty-membership` with membership id) or redeem path which also links → **Mark as paid**. Re-check membership balance increased by earn rate; paying again must not double-earn.

6. **Redeem:** Unpaid order → Mark as paid modal → paste member token → **Redeem loyalty reward**. Expect discount line and reduced amount due (`data-testid=loyalty-discount-line`). Insufficient balance → 400.

7. **Permissions:** Waiter can redeem; waiter **cannot** `PUT /loyalty/program` (403). Admin can adjust (`POST /loyalty/memberships/{id}/adjust`).

8. **i18n:** `python3 scripts/check-i18n-locale-parity.py` → PASS.

9. **Smoke:** `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:4202/` → 200; front Docker logs show no Angular compile errors after reload.
