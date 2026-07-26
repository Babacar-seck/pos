# Import / migration from an existing POS (CSV cutover)

**Status:** MVP shipped (#321) — products + categories via CSV CLI.  
**Related:** umbrella [#52](https://github.com/satisfecho/pos/issues/52), `docs/0050-github-issue-52-split-plan.md` Issue 5, `docs/0032-github-issues-roadmap.md`.

## What it does

Restaurants switching from another system can load a **menu catalog** (product name, price, category, optional subcategory/description/ingredients/cost) with:

1. A documented **sample CSV** and column map.
2. An **idempotent CLI** (`--dry-run` then `--apply`) that validates every row before any write.
3. The same create/update-by-name rules as staff **Products → bulk import** (JSON / vision).

Tables, customers, and historical orders are **out of scope** for this MVP (follow-up).

## Column map (CSV ↔ `Product`)

| CSV column | Required | Maps to | Notes |
|------------|----------|---------|--------|
| `name` | yes | `Product.name` | Match key for idempotent update (case-insensitive, trimmed). |
| `price` | one of price / price_cents | `price_cents` | Major units (e.g. `12.50`); comma decimal accepted. |
| `price_cents` | one of price / price_cents | `Product.price_cents` | Integer cents; must be &gt; 0. |
| `cost` | no | `cost_cents` | Major units. |
| `cost_cents` | no | `Product.cost_cents` | Integer ≥ 0. |
| `category` | no | `Product.category` | Normalized to canonical English keys (e.g. Entrantes → Starters). |
| `subcategory` | no | `Product.subcategory` | Free text. |
| `description` | no | `Product.description` | |
| `ingredients` | no | `Product.ingredients` | Comma-separated list string. |

Unknown columns cause a hard parse error. Header names are case-insensitive. UTF-8 with optional BOM (Excel) is supported. Max **500** data rows per file.

Sample file: `back/fixtures/migration/sample_products.csv`.

## Pre-cutover checklist

1. Confirm the **target tenant id** (never import without `--tenant-id`).
2. Export the old POS menu to CSV; rename columns to the map above.
3. Copy the file into the backend container tree (e.g. `back/fixtures/migration/your_menu.csv` → `/app/fixtures/migration/your_menu.csv`).
4. Prefer a maintenance window; take a DB backup / snapshot if the tenant already has live orders.
5. Run **dry-run** until `invalid=0`.

## Dry-run

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back \
  python -m app.seeds.import_products_csv \
  --tenant-id 1 \
  --csv /app/fixtures/migration/sample_products.csv \
  --dry-run
```

Prints a per-row report (`create` / `update` / `INVALID`) and **writes nothing**. Exit code `1` if any row is invalid; `2` on parse/IO errors.

## Apply

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back \
  python -m app.seeds.import_products_csv \
  --tenant-id 1 \
  --csv /app/fixtures/migration/sample_products.csv \
  --apply
```

- Refuses to write if **any** row is invalid (fix the CSV first).
- Creates new products; **updates** existing products with the same name for that tenant.
- Does not delete products missing from the CSV.

## Rollback

- There is no automatic undo. Prefer dry-run + backup before apply.
- To remove mistaken imports: delete or edit products in the staff **Products** UI, or restore the DB backup.
- Re-running `--apply` with corrected prices/categories is safe for matching names.

## Smoke tests after apply

1. Staff app → **Products**: new/updated names and categories visible.
2. Public menu / delivery menu for the tenant shows the imported dishes (if those channels are enabled).
3. Optional API: `GET /products` as a tenant owner.
4. Backend unit tests: `python3 -m pytest tests/test_import_products_csv.py -q` inside the `back` container.

## Alternative: staff UI (JSON)

Operators who prefer the UI can convert CSV → JSON `{ "items": [ ... ] }` and use **Products → bulk import** (preview + confirm). Same validation and idempotency; no CLI required.

## Non-goals (MVP)

- Tables, floors, customers, historical orders
- Multi-file / multi-tenant batch in one command
- Automatic mapping from third-party vendor column names
- Images / SKU barcodes / stock quantities in the same CSV
