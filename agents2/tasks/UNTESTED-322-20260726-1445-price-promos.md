# Price promotions engine

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/322
- **322**

## Problem / goal

Add a real **pricing promotions** engine (happy hour, %-off category, BOGO-lite, or coupon codes with time/channel eligibility). Distinct from the social-media post scheduler (#199–#201), which is marketing *communication* only. No pricing/discount rule engine exists today. Loyalty redemption (`docs/0066-club-loyalty.md` / **#327**) currently uses `order.loyalty_discount_cents` as a stopgap — this issue should become the shared discount/audit path. From umbrella **#52** Phase D (`docs/0050-github-issue-52-split-plan.md`). Tax/Factura breakdown must stay correct (`docs/0017-billing-customers-factura.md`, VeriFactu **#326**).

## High-level instructions for coder

- MVP: at least **one** promo type end-to-end (e.g. % off category **or** fixed discount code) with eligibility (time window and/or channel), stackability policy, and an audit snapshot on order lines for reporting/tax.
- Staff UI to create/enable promos; public QR menu should reflect eligible prices live for that type.
- Clarify tax-inclusive pricing: discounted lines must still produce a correct Factura/tax breakdown; do not break VeriFactu numbering (**#326**).
- Align with loyalty redeem (**#327**) so there is **one** discount mechanism on orders, not a second parallel path.
- Tenant-scoped rules; pytest for apply/eligibility/isolation; `CHANGELOG.md` + short `docs/` note; append **Testing instructions**.

## Implementation notes (coder)

- MVP type: `percent_off_category` only.
- Migration `20260726171000_price_promotions.sql`; service `promo_service.py`; shared order-level helper `order_discounts.order_level_discount_cents` (loyalty).
- Staff: Settings → Promotions; APIs `/promos`.
- Docs: `docs/0068-price-promotions.md`.

## Testing instructions

1. **Migrate:** `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python -m app.migrate` — expect schema version ≥ `20260726171000`.
2. **Pytest:** `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python3 -m pytest tests/test_price_promotions.py -q` — all pass (tenant isolation, channel/time eligibility, menu live price, order-line audit, best-% wins, loyalty helper).
3. **Staff UI:** Log in as owner/admin → **Settings → Promotions** → create e.g. 20% off category `Beverages`, channel all or `table`. Toggle enabled/disabled.
4. **QR menu:** Open an active table menu; beverage products in that category show discounted `price_cents` and struck-through list price / promo label when eligible.
5. **Order:** Add a promo-eligible item via public menu; order line should have `list_price_cents`, `discount_cents`, `promo_id`, `promo_snapshot`; tax recomputed from discounted inclusive price.
6. **Isolation:** Promo created for tenant A must not appear for tenant B (`GET /promos`).
7. **Smoke:** `BASE_URL=http://127.0.0.1:4202 npm run test:landing-version --prefix front` (or HAProxy port from `docker compose ps`).
8. **Front build:** `docker logs --since 10m pos-front` — no TS/NG compile errors after Settings/menu changes.
