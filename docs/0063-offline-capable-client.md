# Offline-capable POS client (#319)

**Status:** Phase 0 ADR + MVP prototype (staff cash sale sync)  
**Related:** umbrella [#52](https://github.com/satisfecho/pos/issues/52) Issue 4 in [0050](0050-github-issue-52-split-plan.md); fiscal caveats [#203](https://github.com/satisfecho/pos/issues/203) / [0018](0018-verifactu-fiscal-invoicing.md)

## Decision summary

| Topic | Choice |
|-------|--------|
| **MVP surface** | Staff-only: one **cash** take-away (or named take-away table) sale queued offline, synced with an **idempotency key**. |
| **Not in MVP** | Customer QR menu offline, card/Stripe/Revolut, fiscal invoice issue while offline, multi-hour multi-device conflict merge. |
| **Target offline duration** | **Minutes to ~2 hours** of intermittent Wi‑Fi / backend blips during service — not “full day airplane mode”. |
| **Read path** | Local product + take-away table cache refreshed while online (no service worker yet). |
| **Write path** | Browser `localStorage` queue → authenticated `POST /orders/offline-cash` on reconnect. |
| **Conflict rule** | Server wins on idempotency key: first accepted payload is canonical; retries with the **same key** return the existing order (no double sale). |

## Architecture (MVP)

```text
Staff device                    Backend (tenant-scoped)
─────────────                   ───────────────────────
ConnectivityService ──ping──►   GET /health
Product/table cache (LS)
Offline cash UI ──enqueue──►    localStorage queue
     │ online + auth
     └─ flush ───────────────►  POST /orders/offline-cash
                                   idempotency_key UNIQUE(tenant_id, key)
                                   → create order + items + mark paid cash
                                   → OfflineOrderIdempotency row
```

- Reuses existing auth, tenant scoping, product resolution, and cash `payment_method` — **no parallel unauthenticated order API**.
- Fiscal numbering stays **online-only**: do not call fiscal issue from the offline queue in MVP.
- Stripe/Revolut intents require connectivity; offline UI only offers **cash**.

## Threat model (MVP)

| Risk | Mitigation |
|------|------------|
| **Duplicate orders** on flaky sync | Client UUID `idempotency_key`; unique `(tenant_id, key)`; replay returns same `order_id`. |
| **Fraud / forged offline sales** | Same JWT + `order:update_status` + `order:mark_paid` as finish/cash pay; no public offline write. |
| **Fiscal/VeriFactu gaps** | Offline cash does **not** allocate fiscal numbers; staff issue invoices after sync when online. |
| **Clock skew** | Server `paid_at` / `created_at` use server UTC; optional `client_created_at` is advisory only (logged/ignored for sequencing). |
| **Stale prices** | Cache may be outdated; server re-prices from current `Product` at sync time. Staff should refresh cache when online. |
| **Wrong table** | MVP prefers take-away table names; table must belong to tenant. |
| **Device theft with queue** | Queue holds product ids + quantities (no card data); auth token still required to sync — logout clears ability to flush until re-login. |

## Conflict / double-submit rules

1. Generate `idempotency_key` **once** when the staff confirms the offline sale; never regenerate on retry.
2. Successful HTTP 200/201 with that key → mark queue item synced; do not re-POST.
3. Network error / 5xx → keep queued; retry with same body + key.
4. 4xx validation (unknown product, bad table) → mark failed with server detail; do not infinite-retry.
5. Do **not** invent a second client-side “local order id” as the business key — only the idempotency key + server `order_id` after sync.

## Phases (beyond MVP)

1. Service worker + IndexedDB for menu assets.
2. Broader staff writes (add item to open table) with richer conflict UI.
3. Optional cash-only tips; still no card offline.
4. Explicit fiscal offline policy if regulators allow deferred numbering (likely never for VeriFactu live).

## Acceptance (this ship)

- [x] Written ADR + threat model (this doc).
- [x] Prototype: staff cash sale offline → sync on reconnect via idempotent API.
- [x] Clear UI indicator for offline / pending sync.
