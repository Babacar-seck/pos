# Demo delivery missing images

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/312
- **312**

## Problem / goal

Public Satisfecho Delivery at **https://satisfecho.de/delivery/1** shows broken product images. Local HAProxy logs in the same window show repeated **404** for:

- `/uploads/1/products/7637d8f9-1d71-40ae-8760-ca2599537ec5.jpg`
- `/uploads/providers/5ceaad6e-0966-492a-a059-60d19602cf6a/products/20b89c63-db42-4967-b858-5ddc70a71ffb.jpg`

Likely causes (investigate; do not assume one): DB `image_filename` pointing at missing files under `back/uploads/`, demo products not linked to catalog images, or routing/static serving for nested `/uploads/...` paths (see **`docs/0027-amvara9-menu-images-troubleshooting.md`**). Delivery menu should show real images or clear placeholders — not broken `<img>` URLs.

Related ops/seeds: `seed_demo_products`, `link_demo_products_to_catalog`, `clear_orphan_provider_product_images` (indexed in **`docs/testing.md`**). Delivery surface: **`docs/0053`** / public `/delivery/{tenantId}`. Prior archive on catalog orphans: `CLOSED-0-20260604-1325-catalog-provider-images-404-missing-on-disk.md`.

## High-level instructions for coder

- Reproduce on production (`/delivery/1`) and local HAProxy (`http://127.0.0.1:4202/delivery/1`); note which image URLs 404 and whether files exist on disk under `back/uploads/`.
- Trace how public delivery product payloads set image URLs (tenant product vs provider catalog). Prefer fixing seed/link/orphan cleanup or deploy bootstrap so demo tenant 1 has consistent images after reset/deploy — avoid one-off manual file copies that drift again.
- If refs point at missing files, clear orphans or re-link via existing seeds; if files exist but HTTP 404, follow **`docs/0027-amvara9-menu-images-troubleshooting.md`** (explicit upload routes / HAProxy path).
- Confirm both local and production delivery pages load images (or intentional placeholders) without 404 spam in HAProxy logs.
- Add or extend a smoke (Puppeteer or seed check) so demo delivery images stay covered; append **Testing instructions**.
- Do **not** invent a parallel log **`NEW-`** for the same 404s — this FEAT owns the incident.

## Implementation notes (coder)

**Root cause:** Delivery `productImageUrl()` returned paths starting with `/` unchanged. Browser requested bare `/uploads/...`, HAProxy routed to **front** → 404. Files were on disk; `/api/uploads/...` already returned 200 locally and on prod for current menu images. Public menu already prefixed `environment.apiUrl`.

**Changes:**
- `front/src/app/delivery/delivery-checkout.component.ts` — prefix `/uploads/...` with `apiUrl` (same as public-menu).
- `back/app/public_tenant_menu.py` — omit `image_url` when the file is missing on disk (placeholders instead of 404 spam).
- `front/scripts/test-delivery-checkout.mjs` — assert `/api/uploads` srcs + no bare-/uploads 404s; fill postal when required.
- Docs: `docs/testing.md`, `docs/0027-amvara9-menu-images-troubleshooting.md`.
- Tests: `back/tests/test_public_tenant_menu.py` (missing vs existing file).

## Testing instructions

1. **Local smoke (required):**
   ```bash
   BASE_URL=http://127.0.0.1:4202 TENANT_ID=1 npm run test:delivery-checkout --prefix front
   ```
   Expect: `Product images OK (... via /api/uploads/, no bare-/uploads 404s)`, then cart/order create PASS.

2. **Manual local:** Open `http://127.0.0.1:4202/delivery/1`. Product images should load (not broken icons). HAProxy should **not** log 404 for bare `GET /uploads/...` on that page load (requests go to `/api/uploads/...` → back 200).

3. **Backend unit:**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T back python3 -m pytest tests/test_public_tenant_menu.py -q
   ```

4. **After deploy to production:** Open `https://satisfecho.de/delivery/1` and confirm images load. Optional: same Puppeteer with `BASE_URL=https://satisfecho.de`.

## Test report

- **Date/time (UTC):** 2026-07-26 06:49:16 start → 06:50:06 end
- **Log window:** ~06:49–06:50 UTC (local HAProxy/front/back); production browser check ~06:49–06:50 UTC
- **Environment:** `docker-compose.yml` + `docker-compose.dev.yml`; `BASE_URL=http://127.0.0.1:4202`; branch `development` @ `d9fcc145`; production `https://satisfecho.de` still on app-version **2.1.92** / merge `522369e2` (fix not deployed)
- **What was tested:** Delivery product image URL prefix (`/api/uploads`), local smoke + HAProxy, pytest public menu, production `/delivery/1`

### Results

1. **Local smoke `test:delivery-checkout` — PASS.** Output: `Product images OK (7 via /api/uploads/, no bare-/uploads 404s)`; cart/order create OK (id=2354); overall `PASS`.
2. **Manual local `/delivery/1` — PASS.** Browser: 7 product imgs via `/api/uploads/...`, `bareCount=0`, `brokenCount=0` (e.g. Café americano 1920×1200). HAProxy since 3m: `bare_uploads_count=0`, `api_uploads_200=12`.
3. **Backend unit `tests/test_public_tenant_menu.py` — PASS.** `15 passed` in 1.29s.
4. **Production `/delivery/1` — FAIL.** Page still uses bare `https://satisfecho.de/uploads/...` for products (`bareCount=7`, broken imgs). Network: `GET .../uploads/providers/05debe46-.../b5bf4456-....jpg` → **404**; same path under `/api/uploads/...` → **200**. Landing meta still **2.1.92**; fix is **uncommitted** on the local tree (`delivery-checkout.component.ts`, `public_tenant_menu.py`, etc.) — not on `origin/master`, so amvara9 cannot serve it yet.

### Overall: **FAIL**

Failed criterion: **4 (production images after deploy)**. Local 1–3 pass with the working-tree fix; production remains broken until the change is committed, promoted, and deployed.

### Product owner feedback

Locally the delivery page looks fixed: images load through `/api/uploads` and HAProxy no longer 404s bare `/uploads` on that flow. Production demo delivery still shows broken product images because the old client still requests bare `/uploads/...`. Ship the front/back fix (commit on `development`, promote/deploy) and re-verify `https://satisfecho.de/delivery/1` before calling this done.

### URLs tested

1. http://127.0.0.1:4202/delivery/1
2. https://satisfecho.de/delivery/1
3. https://satisfecho.de/uploads/providers/05debe46-d6a8-4b7d-8484-fd6fd26a2de9/products/b5bf4456-1cf8-412c-9539-b40d595ffac2.jpg (404)
4. https://satisfecho.de/api/uploads/providers/05debe46-d6a8-4b7d-8484-fd6fd26a2de9/products/b5bf4456-1cf8-412c-9539-b40d595ffac2.jpg (200)
5. http://127.0.0.1:4202/api/uploads/1/products/7637d8f9-1d71-40ae-8760-ca2599537ec5.jpg (200)
6. https://www.satisfecho.de/api/health (`{"status":"ok"}`)

### Relevant log excerpts (last section)

```
# Local smoke
Product images OK (7 via /api/uploads/, no bare-/uploads 404s)
PASS

# pytest
15 passed, 1 warning in 1.29s

# Local HAProxy after manual /delivery/1 (no bare /uploads)
bare_uploads_count=0
api_uploads_200=12
… "GET /api/uploads/1/products/7637d8f9-1d71-40ae-8760-ca2599537ec5.jpg HTTP/1.1" 200 …

# Production network (Chrome DevTools)
GET https://satisfecho.de/uploads/providers/05debe46-…/b5bf4456-….jpg [404]
GET https://satisfecho.de/api/uploads/1/logo/a5fe3bdd-….png [200]
```
