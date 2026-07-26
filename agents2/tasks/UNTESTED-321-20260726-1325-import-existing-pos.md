# Import existing POS / migration toolkit

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/321
- **321**

## Problem / goal

Restaurants switching from another POS need a **repeatable import path** (products, tables, customers; optionally historical orders) so they are not stuck re-entering catalogs by hand. Today only demo/catalog seed imports exist — no generic migration toolkit or cutover runbook. Blocker for real adoption (umbrella **#52** / `docs/0050-github-issue-52-split-plan.md` Issue 5; roadmap `docs/0032-github-issues-roadmap.md`).

## High-level instructions for coder

- Design MVP around **one happy path**: e.g. products + categories from a **sample CSV** with a clear column ↔ model mapping; keep tables/customers/orders as follow-ups unless a thin shared import framework is cheap.
- Prefer an **idempotent** CLI (or minimal admin UI) with **dry-run + validation report** before commit; never corrupt existing tenant data on bad rows.
- Reuse patterns from existing wine/beer/pizza / demo seeds where useful; do not invent a second parallel catalog pipeline.
- Add a short **`docs/`** cutover runbook: pre-checks, dry-run, apply, rollback, smoke tests.
- Cover with tests (validation failures, happy-path import) and a `CHANGELOG.md` entry; append **Testing instructions**.
- Stay tenant-scoped; no cross-tenant writes; no secrets or live customer PII in fixtures.

## Implementation notes

- Reused existing `app.product_bulk_import` preview/confirm (same idempotency as Products → bulk import JSON).
- Added `parse_products_csv` + CLI `python -m app.seeds.import_products_csv`.
- Sample: `back/fixtures/migration/sample_products.csv`.
- Runbook: `docs/0062-pos-migration-import.md`.
- Follow-ups (not in MVP): tables, customers, historical orders.

## Testing instructions

1. **Unit tests (required):**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T back \
     python3 -m pytest tests/test_import_products_csv.py tests/test_product_bulk_import.py -q
   ```
   Expect all passed.

2. **CLI dry-run (no writes):**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T back \
     python -m app.seeds.import_products_csv \
     --tenant-id 1 \
     --csv /app/fixtures/migration/sample_products.csv \
     --dry-run
   ```
   Expect `invalid=0` and `[dry-run] no database writes.`

3. **Invalid CSV refuses apply:** create a temp CSV with a blank `name` or `price=0`; run with `--apply`; expect exit code `1` and **no** new products for that tenant.

4. **Optional apply on a scratch tenant** (not required on demo tenant 1 if you want to keep the menu clean): run `--apply` once, confirm products appear in staff **Products**; re-run `--apply` and confirm updates (same names) rather than duplicates.

5. **Docs:** skim `docs/0062-pos-migration-import.md` column map + checklist; `CHANGELOG.md` Unreleased mentions #321.
