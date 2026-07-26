# Multi-warehouse inventory per tenant

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/320
- **320**

## Problem / goal

Inventory today is **single-location** (global SKU count). Staff need **multiple stock locations** per tenant (e.g. main kitchen, cold room, bar) so receive/adjust/moves and purchasing can be tied to a **warehouse**. From umbrella **#52** (“multiple almacenes”); see `docs/0050-github-issue-52-split-plan.md` Issue 1 and `docs/0032-github-issues-roadmap.md`. Non-goals for MVP: full WMS picking, barcode multi-bin.

## High-level instructions for coder

- Add a tenant-scoped **`Warehouse`** (or equivalent) model + migration; optional `warehouse_id` on at least one existing inventory flow (e.g. purchase-order receiving / stock move).
- UX: staff can define ≥1 named warehouse beyond an implicit default; choose warehouse on receive/adjust; stock dashboard filterable by location.
- Align with current Inventory nav / purchase-order / supplier patterns; keep tenant scoping and auth consistent with adjacent endpoints.
- Migrations + backend tests; `CHANGELOG.md` entry; append **Testing instructions**.
- Do not scope full multi-branch central-kitchen logistics in this slice.

## Implementation notes

- Migration `back/migrations/20260726132730_inventory_warehouse.sql`: `warehouse`, `warehouse_stock`; `warehouse_id` on `inventory_batch` / `inventory_transaction`; seeds default **Main** per tenant and backfills existing stock.
- API: `GET/POST /inventory/warehouses`, `PUT/DELETE /inventory/warehouses/{id}`; optional `warehouse_id` on adjust + PO receive; `GET /inventory/stock-levels?warehouse_id=`.
- Front: Inventory → Warehouses; warehouse picker on adjust + receive; stock dashboard location filter.
- Docs: `docs/0061-multi-warehouse-inventory.md`; roadmap/CHANGELOG updated.
- Tests: `back/tests/test_inventory_warehouses.py` (6 passed).

## Testing instructions

1. **Migration:** From repo root with stack up:  
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T back python -m app.migrate`  
   Expect schema version includes `20260726132730`.

2. **Backend tests:**  
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T back python3 -m pytest tests/test_inventory_warehouses.py -q`  
   Expect **6 passed**.

3. **API smoke (owner/admin with inventory):**  
   - `GET /inventory/warehouses` → at least one default **Main**.  
   - `POST /inventory/warehouses` with `{"name":"Cold room","code":"COLD"}` → 200.  
   - Adjust an item with `warehouse_id` for Cold room; `GET /inventory/stock-levels?warehouse_id=<cold_id>` shows the qty there and Main remains unchanged for that item (if it started empty).

4. **UI:** Log in as inventory-capable admin → Inventory → **Warehouses** → create a second warehouse → Items → Adjust Stock → choose warehouse → Stock Dashboard → filter by that warehouse. Open an approved PO → Receive → confirm warehouse selector.

5. **Front health:** `BASE_URL=http://127.0.0.1:4202 npm run test:landing-version --prefix front` (or current HAProxy port). Confirm front logs show no TS/NG build errors after load.
