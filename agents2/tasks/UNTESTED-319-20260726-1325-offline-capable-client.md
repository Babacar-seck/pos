# Offline-capable POS client

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/319
- **319**

## Problem / goal

Critical staff flows (take order, cash payment) fail when WiFi or the cloud backend drops mid-service. Need an **offline-capable client** with sync on reconnect. Large architecture change (service worker, local persistence, idempotent APIs, conflict resolution). From umbrella **#52**; see `docs/0050-github-issue-52-split-plan.md` Issue 4. Fiscal/VeriFactu sequential numbering and Stripe intents are high-risk offline — treat carefully (related caveats around **#203**).

## High-level instructions for coder

- **Phase 0 first:** write a short architecture ADR + threat model (duplicate orders, fraud, fiscal numbering gaps, clock skew). Decide which surface is MVP (staff order-taking vs customer QR) and target offline duration.
- MVP prototype: **one** staff action (e.g. take a **cash** order) works offline and syncs cleanly on reconnect with idempotency keys; clear UI indicator for offline mode.
- Prefer read-only menu/product cache before a full write queue; card/Stripe offline is out of scope for MVP (cash-only).
- Document conflict-resolution and “do not double-submit” rules; avoid inventing parallel order APIs that bypass tenant/auth.
- Tests for sync/idempotency where practical; `CHANGELOG.md` / docs ADR path; append **Testing instructions**.

## Implementation summary (010)

- ADR + threat model: `docs/0063-offline-capable-client.md`
- Backend: `POST /orders/offline-cash` + `offline_order_idempotency` ledger; service in `back/app/offline_order_service.py`
- Frontend: connectivity banner in staff sidebar; Orders page “Offline cash sale” panel; localStorage product/table cache + queue; sync on reconnect
- Tests: `back/tests/test_offline_cash_order.py` (create + idempotent replay + tenant isolation)

## Testing instructions

1. **Migrate:** `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python -m app.migrate` — expect version ≥ `20260726153500`.
2. **Pytest:** `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python3 -m pytest tests/test_offline_cash_order.py -q` — expect 2 passed.
3. **Smoke:** `BASE_URL=http://127.0.0.1:4202 npm run test:landing-version --prefix front` — landing + staff nav OK.
4. **Manual offline cash (staff):**
   - Log in as owner/waiter with mark-paid permission; open `/staff/orders`.
   - Confirm “Offline cash sale” panel; wait for product cache (or click Refresh cache). Need a **Take Away** table.
   - DevTools → Network → Offline (or disable Wi‑Fi). Banner should show offline.
   - Queue a cash sale (product + qty). Item stays pending in the list.
   - Go online again; within ~15s (or reload) pending item should sync to a paid order (`#id` shown). Repeat the same sale should not create a second order if the same idempotency key is reused (automatic on flush).
5. **Idempotency API:** POST `/api/orders/offline-cash` twice with the same `idempotency_key` — second response `status: "duplicate"` and same `order_id`.
6. **Out of scope check:** fiscal issue / Stripe not offered in the offline panel (cash only).
