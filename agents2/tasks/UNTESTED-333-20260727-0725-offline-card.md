# Finish offline card / fiscal offline

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/333
- **333**

## Problem / goal

Offline-capable staff client MVP shipped under **#319** (`docs/0063-offline-capable-client.md`): cash-only offline Take Away sale + idempotent `POST /orders/offline-cash` sync. Closing notes and ADR explicitly left **card/Stripe/Revolut offline** and **fiscal invoice issue while offline** as future work. This issue finishes that remaining offline-card / fiscal-offline slice on top of the existing queue.

## High-level instructions for coder

- Read `docs/0063-offline-capable-client.md`, VeriFactu caveats in `docs/0018-verifactu-fiscal-invoicing.md` / related #203 notes, and closed `agents2/tasks/done/2026/07/26/CLOSED-319-20260726-1325-offline-capable-client.md`.
- Prefer a **safe incremental** slice: do not invent card capture that stores PAN/CVV on device. Prefer deferred online card after reconnect (queue intent metadata only) or document why true offline card is blocked.
- **Fiscal:** keep VeriFactu/live numbering **online-only** unless an explicit deferred-numbering policy is approved and documented; offline queue must not allocate fiscal series while disconnected.
- Extend the existing offline queue/UI patterns (connectivity banner, localStorage cache, idempotency ledger) rather than a second offline pipeline; preserve tenant/auth on sync.
- Update ADR phases in `docs/0063-offline-capable-client.md` with the chosen card/fiscal policy; pytest for any new sync/idempotency paths; `CHANGELOG.md`; append **Testing instructions**.

## Implementation summary (010)

- **Policy (ADR `docs/0063`):** True offline card capture blocked (no PAN/CVV). Deferred card: queue `payment_intent=card` → sync creates **unpaid** take-away order; staff collects card online. Fiscal/VeriFactu numbering stays **online-only after payment** (note in `docs/0018`).
- **Backend:** `OfflineCashOrderCreate.payment_intent` (`cash`|`card`); `create_offline_cash_order` branches; response adds `payment_intent` + `needs_payment`. Same idempotency ledger; no new migration.
- **Frontend:** Offline sale panel payment select; queue stores intent; sync passes intent; list shows “collect card online” when `needs_payment`.
- **Tests:** `tests/test_offline_cash_order.py` — deferred card unpaid + idempotent replay + invalid intent (4 passed).
- **CHANGELOG** Unreleased + i18n parity OK.

## Testing instructions

1. **Pytest:**  
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python3 -m pytest tests/test_offline_cash_order.py -q`  
   Expect **4 passed** (cash create/replay, tenant isolation, TSE cash auto-sign, deferred card unpaid + idempotency + bad intent).

2. **Smoke:** `BASE_URL=http://127.0.0.1:4202 npm run test:landing-version --prefix front` — landing + staff nav OK (includes `/staff/orders`).

3. **i18n:** `python3 scripts/check-i18n-locale-parity.py` — PASS.

4. **Manual deferred card (staff):**
   - Log in with mark-paid permission; open `/staff/orders`.
   - Offline sale panel: Payment = **Card (pay after sync)**; pick product; DevTools → Network → Offline; queue sale.
   - Go online; pending item syncs to an **unpaid** order (`#id` + “collect card online”). Open that order and mark paid / card via normal UI.
   - Confirm queue item never asked for card number.

5. **API:** `POST /api/orders/offline-cash` with `payment_intent: "card"` twice same `idempotency_key` → second `status: "duplicate"`, same `order_id`, `needs_payment: true`, `paid_at: null`.

6. **Out of scope check:** No fiscal issue / VeriFactu call from offline sync; offline panel does not capture PAN/CVV; cash path still creates paid orders.
