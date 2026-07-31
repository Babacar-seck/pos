# Signup enhance (end-user customer accounts)

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/340
- **340**

## Problem / goal

**End-user customer accounts** are not shipped: registration, login, email verification, MFA, account-based order history, and customer-facing self-serve invoices. Staff **Factura CRM** (`/customers`) and fiscal invoice on orders are already live — do **not** conflate or rebuild that path.

Design notes (historical / partial status): **`docs/0002-customer-features-plan.md`**. Treat detailed schema sections as design input; align with current models, auth, and mail patterns in the live codebase.

## High-level instructions for coder

- Read **`docs/0002-customer-features-plan.md`** (status banner + auth/order/invoice sections) and map against what already exists (staff Billing Customers / Factura vs missing end-user portal).
- Deliver a **first vertical slice** of end-user customer signup/login (and email verification if mail infra allows), then order history and self-serve invoices only if the slice is stable — prefer incremental shippable steps over a big-bang of MFA + invoices in one WIP.
- Keep **Customer** identity separate from restaurant **User** (staff/owner); tenant-safe linking of orders to customers; no cross-tenant reads.
- Reuse existing auth, mail, and i18n patterns; do not invent a second staff CRM. MFA is in the plan but may follow as a later task if core register/login/verify lands first — note deferrals in the task file.
- **Out of scope:** rewriting staff Factura CRM; changing SaaS restaurant signup/paywall (`docs/0052`) unless a shared auth primitive is strictly required.
- **Docs / tests:** update `docs/0002` status if behavior ships; add or extend Puppeteer/API smoke for the customer flow; append **Testing instructions** when moving to UNTESTED.
- Pass criteria: a clear end-user path exists (or is documented as the agreed first slice) for customer registration/login without relying on staff accounts; staff Factura remains intact.

## Security note (001)

Issue body summarized for product intent only; no secrets copied.

## Implementation notes (010)

### Shipped (first slice)

- Migration `back/migrations/20260731114840_add_end_user_customer.sql`: table `customer`, nullable `order.customer_id`.
- Model `Customer` (distinct from `User` and `BillingCustomer`); API under `/customer/*` (`customer_routes.py`).
- Auth cookie `customer_access_token` (JWT `type=customer`); does not reuse staff `access_token`.
- Endpoints: `POST /customer/register`, `POST /customer/token`, `POST /customer/logout`, `GET /customer/me`, `GET /customer/verify-email`, `POST /customer/resend-verification`, `GET /customer/orders`.
- SPA: `/customer/register`, `/customer/login`, `/customer/verify-email`, `/customer` (guarded home with empty/list orders + resend verify).
- Email verification via global SMTP + `PUBLIC_APP_BASE_URL` (same pattern as password reset); if unset, register still succeeds with `verification_email_sent: false`.
- Docs: `docs/0002` status banner, `docs/testing.md`, `AGENTS.md` Key URLs, CHANGELOG Unreleased.
- Tests: `back/tests/test_customer_accounts.py` (7), `npm run test:customer-register-login`.

### Deferred (follow-up tasks)

- MFA / TOTP for customers.
- Self-serve tax invoices / PDF.
- Auto-attach `customer_id` on public menu / delivery order create when customer cookie present.
- Customer profile edit (business_name, tax_id, address) UI beyond fields stored on model.

## Testing instructions

1. **Migrate (if needed):** `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python -m app.migrate` — expect `20260731114840_add_end_user_customer`.
2. **Backend pytest:**  
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python3 -m pytest tests/test_customer_accounts.py -q`  
   Expect **7 passed**.
3. **API smoke:**  
   `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:4202/api/customer/me` → **401**.  
   `curl -s -X POST http://127.0.0.1:4202/api/customer/register -H 'Content-Type: application/json' -d '{"email":"cust-test-$(date +%s)@amvara.de","password":"testpass123","full_name":"T"}'` → **201** with `email_verified: false`.
4. **Puppeteer:**  
   `BASE_URL=http://127.0.0.1:4202 npm run test:customer-register-login --prefix front` → **PASS** (register → login → empty orders).
5. **Staff Factura intact:** open `/customers` as staff (existing login) — still Billing Customers CRM; must not require end-user `Customer` cookie.
6. **Optional email verify:** with `PUBLIC_APP_BASE_URL` and SMTP set, register and open the emailed `/customer/verify-email?token=…` link; `/customer` should show email verified.
7. **Front build:** `docker logs --since 10m pos-front` — no TS/NG compile errors after customer pages load.
