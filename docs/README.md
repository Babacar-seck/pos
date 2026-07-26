# POS2 Documentation

This folder contains deployment guides, feature documentation, implementation plans, and reference notes. The main [README.md](../README.md) and [ROADMAP.md](../ROADMAP.md) in the repo root link to specific docs below.

---

## Quick links

| Need to… | See |
|----------|-----|
| Set up Revolut (sandbox, redirects, certificates) | [REVOLUT.md](REVOLUT.md) |
| Run Puppeteer/UI tests | [testing.md](testing.md) |
| Multi-agent task loop + GitHub Issues handoff | [agent-loop.md](agent-loop.md) |
| Deploy to a server | [0004-deployment.md](0004-deployment.md) |
| Set up CI/CD (amvara9) | [0001-ci-cd-amvara9.md](0001-ci-cd-amvara9.md) |
| Configure Gmail for email | [0056-gmail-setup.md](0056-gmail-setup.md) |
| Troubleshoot missing reservation confirmation email | [0030-reservation-confirmation-email-troubleshooting.md](0030-reservation-confirmation-email-troubleshooting.md) |
| Understand reservations / waiting list (staff + public) | [0011-table-reservation-user-guide.md](0011-table-reservation-user-guide.md) |
| Guest / staff Satisfecho Delivery (checkout, courier, track) | [0053-satisfecho-delivery-order-channel.md](0053-satisfecho-delivery-order-channel.md) |
| Enable or understand SaaS signup paywall (keep off until runbook) | [0052-saas-signup-paywall.md](0052-saas-signup-paywall.md) |
| Platform operator oversight (`/platform`) | [0059-platform-operator-portal.md](0059-platform-operator-portal.md) |
| Manage multi-location restaurant groups | [0054-restaurant-groups.md](0054-restaurant-groups.md) |
| Rate limits (production) | [0020-rate-limiting-production.md](0020-rate-limiting-production.md) |
| Capture screenshots | [screenshots/README.md](screenshots/README.md) |
| Security review notes (structured pass, not a pentest) | [SECURITY-REVIEW.md](SECURITY-REVIEW.md) |
| Browse public marketing features list (`/features`, no login) | [../README.md](../README.md) Access Points / Features — route `http://localhost:4202/features` |

---

## Deployment & operations

| Doc | Description |
|-----|-------------|
| [0001-ci-cd-amvara9.md](0001-ci-cd-amvara9.md) | CI/CD: deploy to amvara9 on push to master (GitHub Actions, SSH key, secrets); daily demo data reset cron for tenant 1; hourly unpaid public Satisfecho Delivery cleanup cron (all tenants). |
| [0004-deployment.md](0004-deployment.md) | Deployment guide: configuration (API_URL, WS_URL, CORS), deploy steps (git pull, compose, migrations, seeds, optional demo reset). See also [0027](0027-amvara9-menu-images-troubleshooting.md) for uploads 404. |
| [0057-deploy-css-fix-amvara9.md](0057-deploy-css-fix-amvara9.md) | **Shipped:** stale front build on deploy — `deploy-amvara9.sh` `--no-cache` front + `index.html` no-cache headers; historical incident notes. |
| [0026-haproxy-ssl-amvara9.md](0026-haproxy-ssl-amvara9.md) | HAProxy SSL on amvara9: durable cert path (certbot/haproxy-certs), reload without overwriting certs. See also [0027](0027-amvara9-menu-images-troubleshooting.md) for uploads 404. |
| [0027-amvara9-menu-images-troubleshooting.md](0027-amvara9-menu-images-troubleshooting.md) | amvara9 public menu/catalog image 404s on `/api/uploads/…` — **ops guide; upload routes shipped**; JSON `Image not found` → missing file / orphan DB ref (not StaticFiles redeploy). |
| [0029-deployment-images-plan-next-month.md](0029-deployment-images-plan-next-month.md) | **Deferred / not scheduled:** Future deploy-via-images plan (CI → registry → pull, two-slot). Current production path remains [0001](0001-ci-cd-amvara9.md) / [0004](0004-deployment.md). |

---

## Email & SMTP

| Doc | Description |
|-----|-------------|
| [0005-email-sending-options.md](0005-email-sending-options.md) | **Research only** — provider comparison (Proton, SendGrid, Resend, Gmail); not a shipping checklist. Ops: [0056](0056-gmail-setup.md), [0030](0030-reservation-confirmation-email-troubleshooting.md). |
| [0056-gmail-setup.md](0056-gmail-setup.md) | Gmail setup: create account, 2FA, App Password, POS Settings → Email (SMTP). |
| [0030-reservation-confirmation-email-troubleshooting.md](0030-reservation-confirmation-email-troubleshooting.md) | **Ops:** booking has email but no confirmation — diagnose script, log strings, tenant vs global SMTP. |

---

## Feature guides (user-facing)

| Doc | Description |
|-----|-------------|
| [0011-table-reservation-user-guide.md](0011-table-reservation-user-guide.md) | Table reservations: staff flows, public booking at `/book/:tenantId`, view/cancel at `/reservation?token=...`; public waiting list at `/waitlist/:tenantId` and staff Waiting list tab. |
| [0014-provider-portal.md](0014-provider-portal.md) | Provider (supplier) portal at `/provider` — not the courier portal (`/courier`; see [0053](0053-satisfecho-delivery-order-channel.md)). |
| [0015-kitchen-display.md](0015-kitchen-display.md) | Kitchen display: full-screen at `/kitchen` (and `/bar`), auto-refresh, WebSocket, optional sound; Satisfecho Delivery cards use table label “Satisfecho Delivery” (not shown once `out_for_delivery`); highlighted order/item comments (#284). |
| [0016-reports.md](0016-reports.md) | Reports (Sales & Revenue): date range, summary (incl. overbooking slots when &gt; 0), by product/category/table/waiter, CSV/Excel export. |
| [0017-billing-customers-factura.md](0017-billing-customers-factura.md) | Billing customers (Factura): register company details, search, print invoice with “Bill to”. See also VeriFactu [0018](0018-verifactu-fiscal-invoicing.md). |
| [0018-verifactu-fiscal-invoicing.md](0018-verifactu-fiscal-invoicing.md) | VeriFactu-oriented fiscal invoicing: tenant `fiscal_mode` (off/test/live), server-issued fiscal stub (series/number), Factura QR/disclaimer; **no production AEAT submission yet**. |
| [0028-tenant-public-branding.md](0028-tenant-public-branding.md) | Tenant public branding (shipped): background colour and header image for book, menu, reservation-view, waitlist, and guest feedback. |
| [0059-platform-operator-portal.md](0059-platform-operator-portal.md) | Platform operator portal: SaaS metrics and tenant oversight. |
| [0051-table-groups-mvp.md](0051-table-groups-mvp.md) | Floor-plan table join/unjoin (**shipped** reference): combined seats and reservation pool for joined tables — not restaurant multi-location groups ([0054](0054-restaurant-groups.md)). |
| [0052-saas-signup-paywall.md](0052-saas-signup-paywall.md) | Hard paywall for restaurant signups: trial/subscribe before staff app (issue #296). Includes guided `/register`/`/signup` wizard steps and 402-exempt priming paths. Keep off until ready; production enablement checklist in the doc (see also amvara9 § SaaS paywall in 0001). |
| [0053-satisfecho-delivery-order-channel.md](0053-satisfecho-delivery-order-channel.md) | Satisfecho Delivery: staff Delivery tab / courier API, public checkout `/delivery/{tenantId}`, fee/postal/radius coverage, guest track `/delivery/{tenantId}/track`, unpaid public TTL cleanup (issue #297 / #306). |
| [0054-restaurant-groups.md](0054-restaurant-groups.md) | Restaurant groups: multi-location join codes; optional shared billing customers/products (issue #283). |
| [0055-public-seo.md](0055-public-seo.md) | Public SEO for satisfecho.de: titles/meta/OG, robots.txt, sitemap.xml, noindex for staff shells (issue #307). |
| Public `/features` page | Marketing capabilities grid for prospects (no login). Linked from landing nav; shares `app-landing-site-footer`. Indexed in root [README.md](../README.md) Features / Access Points; smoke: `npm run test:features --prefix front` ([testing.md](testing.md)). |
| [REVOLUT.md](REVOLUT.md) | Revolut Merchant API: checkout extension, sandbox CSR, redirect URLs, tenant payment setup. |

---

## Implementation plans & specs

| Doc | Description |
|-----|-------------|
| [0002-customer-features-plan.md](0002-customer-features-plan.md) | Customer features: registration, login, email verification, MFA, order history, invoices. |
| [0008-order-management-logic.md](0008-order-management-logic.md) | Order management: **shipped** session rules / design reference (lifecycle, status reset, edge cases) — not an open backlog. |
| [0009-table-pin-security.md](0009-table-pin-security.md) | Table PIN security: **shipped** (activate / PIN / regenerate / close; public-menu gates); optional GPS flagging off by default — operator/reference. |
| [0010-table-reservation-implementation-plan.md](0010-table-reservation-implementation-plan.md) | Table reservation: **historical** design/API plan (core shipped); use **[0011](0011-table-reservation-user-guide.md)** for live staff/public how-to. |
| [0019-no-show-implementation-plan.md](0019-no-show-implementation-plan.md) | No-show feature: status, reminder emails, implementation steps. |
| [0021-working-plan.md](0021-working-plan.md) | Working plan (shift schedule): living guide — status, API, UI, ops. |
| [0060-working-plan-implementation-plan.md](0060-working-plan-implementation-plan.md) | Working plan: **historical** pre-build plan (BetterShift eval); use **0021** for current behaviour. |
| [0025-reservation-overbooking-detection.md](0025-reservation-overbooking-detection.md) | Reservation overbooking: **shipped** (slot capacity, overbooking report, 400 on over capacity); historical design notes + [0058](0058-test-scenario-one-empty-table.md) scenario. |
| [0058-test-scenario-one-empty-table.md](0058-test-scenario-one-empty-table.md) | Test scenario: all tables seated except one empty (maps 0025 overbooking requirements to this case). |
| [0031-order-customizations-plan.md](0031-order-customizations-plan.md) | GitHub **#50**: pizza-style order modifiers — existing `ProductQuestion` / `customization_answers`, staff UI gap, phased plan. |
| [0032-github-issues-roadmap.md](0032-github-issues-roadmap.md) | GitHub **#52–#54**: umbrella roadmap (warehouses, kitchen SLAs, marketing/comms). |
| [0050-github-issue-52-split-plan.md](0050-github-issue-52-split-plan.md) | GitHub **#52** (CLOSED): **historical** child-issue drafts / phases — do not re-file without review; prefer **0032** + shipped feature docs. |

---

## Reference & notes

| Doc | Description |
|-----|-------------|
| [agent-loop.md](agent-loop.md) | Multi-agent workflow (task statuses, roles, `agents2/tasks/` + prompts; legacy `agents/` may appear in older notes); modeled on mac-stats-reviewer; links to **`go-ahead-loop.sh`** and testing smokes. |
| [agent-cursor-rules.md](agent-cursor-rules.md) | Categorized index of **`.cursor/rules/*.mdc`** for agents (Angular, FastAPI/SQLModel, Docker/HAProxy, security, i18n, smoke tests); also linked from **`AGENTS.md`**. |
| [SECURITY-REVIEW.md](SECURITY-REVIEW.md) | Structured security pass (uploads, auth, tenant isolation, public/payment surfaces) — **not a penetration test**; repeat after major releases. |
| [0007-implementation-verification.md](0007-implementation-verification.md) | **Historical** (2026-01-13) verification snapshot vs 0008 — not live line refs; prefer code/tests + 0008 for current order behaviour. |
| [0012-translation-implementation.md](0012-translation-implementation.md) | Translation (i18n): frontend, backend, DB content. |
| [0013-verification-alternatives.md](0013-verification-alternatives.md) | **Research only** — customer verification alternatives (SMS, OAuth, etc.); not a shipping decision; app uses email/password. |
| [0020-rate-limiting-production.md](0020-rate-limiting-production.md) | Rate limiting: limits (login, register, payment, public menu, upload, admin), Redis, X-Forwarded-For, tests. |
| [0022-oauth-social-login-notes.md](0022-oauth-social-login-notes.md) | OAuth / social login (Google, Microsoft, etc.): notes and recommendation. |
| [0023-prioritisation-019-022.md](0023-prioritisation-019-022.md) | Prioritisation: docs 0019–0022 — **0021 done**; next open item **0022 (OAuth)**. |
| [0024-whatsapp-reminder-notes.md](0024-whatsapp-reminder-notes.md) | WhatsApp reservation reminder: **shipped** Twilio channel (env + send-reminder); historical design notes. |
| [0033-postgres-adhoc-sql-table-names.md](0033-postgres-adhoc-sql-table-names.md) | Ad-hoc SQL: no `restaurantorder` table; use `"order"` / `orderitem`, quoting reserved names. |
| [PRINTING.md](PRINTING.md) | Restaurant LAN / kitchen ticket printing design notes (**not implemented**); browser and invoice print from staff UI are supported today. |

---

## Testing

| Doc | Description |
|-----|-------------|
| [testing.md](testing.md) | **Puppeteer UI tests**: prerequisites, env vars, all test scripts (reservations, demo data, working plan, tables, landing, provider, orders, reports, catalog, rate limit, etc.), npm script table, backend/data checks, coverage summary, known issues. |

---

## Screenshots

| Doc | Description |
|-----|-------------|
| [screenshots/README.md](screenshots/README.md) | How to capture screenshots (Puppeteer script, manual), file list and where each is used (README, feature docs). |

---

## Other

- **banner.svg** — Banner image used in the main README.
