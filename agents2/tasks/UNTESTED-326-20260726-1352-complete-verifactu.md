# Complete VeriFactu (production AEAT path)

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/326
- **326**

## Problem / goal

[#203](https://github.com/satisfecho/pos/issues/203) shipped a per-tenant fiscal **stub** (`fiscal_mode`, numbering, print QR placeholder) documented in `docs/0018-verifactu-fiscal-invoicing.md` — **no real AEAT submission**. Software-vendor VeriFactu/SIF obligations already apply; end-user dates were postponed, but Satisfecho still needs a certifiable production path before any tenant can safely use `fiscal_mode: live`.

## High-level instructions for coder

- **Phase 0 first:** publish a short build-vs-buy ADR (in-house AEAT wire vs certified middleware such as Fiskaly / Verifacti / Efsta). Prefer not inventing AEAT endpoints or payloads.
- Implement in order only after Phase 0: hash chaining, real AEAT verification QR/link, near-real-time sandbox submission in `test` mode, immutability (edit/delete blocked; credit-note cancel path).
- Do **not** enable or market `fiscal_mode: live` until Phases 1–4 are verified against the official spec; keep disclaimer language consistent with #203 / `docs/0018`.
- Coordinate with printing bridge (receipt must carry real QR + mandatory text) and split-bill (sequential numbering across partial payments).
- Add `docs/00XX-verifactu-production.md` (certification status, what live mode does/does not cover) and update public `/features` to match reality, not aspiration.
- Tests for hash chain + sandbox happy path; `CHANGELOG.md`; append **Testing instructions**. No guessed production AEAT calls without verified spec.

## Implementation notes (feature coder)

- **Phase 0 ADR:** `docs/0065-verifactu-production.md` — prefer certified middleware; POS owns numbering, internal hash chain, ValidarQR URL shape, immutability, sandbox hook.
- **Migration:** `back/migrations/20260726142100_fiscal_invoice_hash_chain.sql`
- **Service:** `back/app/fiscal_invoice_service.py` — `pos.fiscal.hash.v1` chain, AEAT ValidarQR URL, sandbox submit (+ optional `FISCAL_MIDDLEWARE_*`), `POST …/fiscal-invoice/cancel` anulación.
- **Live gate:** `FISCAL_LIVE_UNLOCK` + middleware URL required before `fiscal_mode: live`.
- **Docs/UI:** updated `0018`, `/features` + Settings i18n honesty; `CHANGELOG` Unreleased.
- **Deferred / follow-up:** official AEAT huella/SOAP (middleware vendor selection + contract); printing-bridge layout polish; split-bill sequential numbering across partial payments.

## Testing instructions

1. **Migrate:** `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python -m app.migrate` — expect `20260726142100_fiscal_invoice_hash_chain` applied; columns `record_hash`, `previous_hash`, `record_type` on `fiscal_invoice`.
2. **Pytest:** `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python3 -m pytest tests/test_fiscal_invoice_api.py -q` — all green (issue + idempotent, hash chain, sandbox fields, immutability 409, anulación then delete, live mode blocked).
3. **Settings UI:** Log in as owner → Settings → Payments → set fiscal mode to **Test**, save. Attempt **Live** without unlock → expect API/settings rejection (400).
4. **Issue path:** Paid order → Print Factura (or `POST /orders/{id}/fiscal-invoice/issue`) → response includes `record_hash`, `verification_qr_content` containing `ValidarQR`, and `sandbox_submitted_at` set.
5. **Immutability:** After issue, `DELETE /orders/{id}` or edit line quantity → **409**. Then `POST /orders/{id}/fiscal-invoice/cancel` → anulación `record_type`; delete should succeed.
6. **Smoke:** `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:4202/` → 200; front logs have no new TS/NG build errors.
7. **Docs spot-check:** `docs/0065-verifactu-production.md` and `docs/0018-verifactu-fiscal-invoicing.md` describe middleware preference and live gate.
