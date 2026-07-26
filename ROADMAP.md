# Development Roadmap

High-level product status for Satisfecho POS. Prefer this file for “what’s done / what’s next”; use `docs/` for how it works and [`CHANGELOG.md`](CHANGELOG.md) for release history.

**Umbrella tracks:** [#52](https://github.com/satisfecho/pos/issues/52)–[#54](https://github.com/satisfecho/pos/issues/54) detail lives in [`docs/0032-github-issues-roadmap.md`](docs/0032-github-issues-roadmap.md).

---

## How to keep this current (recurring)

Refresh **`ROADMAP.md`** and the **#52** table in **`docs/0032-github-issues-roadmap.md`** whenever:

1. A batch of product issues lands as **`CLOSED-*`** under `agents2/tasks/done/`, or
2. Agent **008** (enhancement reviewer) runs its weekly pass and notices drift vs `CHANGELOG.md`.

Do **not** paste implementation howtos, rate-limit strategy drafts, or secrets here — link to `docs/` instead. Queue a small **`FEAT-0-…-update-roadmap.md`** (or reopen a roadmap issue) when this file lags shipped work.

---

## Shipped (stable)

Core POS and recent 2026-07-26 slices. Links are the source of detail.

| Area | Notes |
|------|--------|
| Orders & kitchen | Lifecycle, soft-delete, comments, customizations ([#50](https://github.com/satisfecho/pos/issues/50)), kitchen display — `docs/0008`, `docs/0015`, `docs/0031` |
| Payments | Stripe; immediate-payment setting; split bill by amount + by line ([#318](https://github.com/satisfecho/pos/issues/318), [#331](https://github.com/satisfecho/pos/issues/331)) — `docs/0071` |
| Reservations & waitlist | Staff + public book/cancel; waiting list — `docs/0011` |
| Delivery | Satisfecho Delivery staff/courier/public — `docs/0053` |
| Billing / fiscal | Factura customers; VeriFactu prep ([#326](https://github.com/satisfecho/pos/issues/326)); German TSE Phase 1 ([#316](https://github.com/satisfecho/pos/issues/316)) — `docs/0017`, `docs/0018`, `docs/0065`, `docs/0072` |
| Inventory | Multi-warehouse MVP ([#320](https://github.com/satisfecho/pos/issues/320)) — `docs/0061` |
| Offline | Staff offline cash sale + sync ([#319](https://github.com/satisfecho/pos/issues/319)) — `docs/0063` |
| Migration | Products/categories CSV import ([#321](https://github.com/satisfecho/pos/issues/321)) — `docs/0062` |
| Promos & loyalty | Category %-off ([#322](https://github.com/satisfecho/pos/issues/322)); club loyalty + birthday bonus ([#327](https://github.com/satisfecho/pos/issues/327), [#331](https://github.com/satisfecho/pos/issues/331)) — `docs/0068`, `docs/0066` |
| Guests | Feedback + Google review URL ([#325](https://github.com/satisfecho/pos/issues/325)); reservation birthdays ([#324](https://github.com/satisfecho/pos/issues/324)) — `docs/0064`, `docs/0067` |
| Multi-site | Restaurant groups; branch hub fulfillment ([#323](https://github.com/satisfecho/pos/issues/323)); floor-plan table join MVP — `docs/0054`, `docs/0069`, `docs/0051` |
| Hardware | LAN print agent / kitchen+receipt jobs ([#317](https://github.com/satisfecho/pos/issues/317)) — `docs/0070` |
| SaaS / platform | Signup paywall; `/pricing`; platform portal — `docs/0052`, `docs/0059` |
| Security | Rate limiting (Redis/slowapi) — `docs/0020`; CAPTCHA still deferred |
| Other | Provider portal, reports, i18n, table PIN, deploy — `docs/0014`, `docs/0016`, `docs/0012`, `docs/0009`, `docs/0004` |

---

## In progress / next

| Item | Status | Tracking |
|------|--------|----------|
| **#52 remaining slices** | Partial — see table in `docs/0032` | Transfers/WMS, deeper offline (SW write queue), more migration entities, Uber Eats |
| **#53 Kitchen SLAs / stations** | Not started | Age gradients, category SLAs, station views — `docs/0015`, issue [#53](https://github.com/satisfecho/pos/issues/53) |
| **#54 Post-visit campaigns** | Partial feedback shipped; SMS/email automation open | [#54](https://github.com/satisfecho/pos/issues/54) |
| **TSE live / VeriFactu live** | Test/stub paths shipped; live gated on certified middleware | `docs/0072`, `docs/0065` |
| **Order customizations price deltas** | Core customizations shipped; priced modifiers optional | [#50](https://github.com/satisfecho/pos/issues/50), `docs/0031` |

Open issues: [github.com/satisfecho/pos/issues](https://github.com/satisfecho/pos/issues).

---

## Deferred

| Item | Why deferred | Notes |
|------|--------------|--------|
| **End-user customer accounts** | Separate from staff Factura CRM | Registration, MFA, self-serve history — `docs/0002` |
| **Order management Phase 4** | Advanced ops | Batch status, audit history, post-payment mods — `docs/0007` |
| **Strict immediate payment** | Product choice | Modal can still be dismissed today |
| **CAPTCHA after failed login** | Nice-to-have on top of rate limits | Listed in `docs/0020` |
| **Aggregator delivery (Uber Eats, etc.)** | Distinct from Satisfecho Delivery | Under #52 |
| **Warehouse transfers / full WMS** | Beyond multi-warehouse MVP | Under #52 |

---

## Related

- [`CHANGELOG.md`](CHANGELOG.md) — what shipped in each version
- [`docs/README.md`](docs/README.md) — doc index
- [`docs/0032-github-issues-roadmap.md`](docs/0032-github-issues-roadmap.md) — #52–#54 theme table
- [`docs/agent-loop.md`](docs/agent-loop.md) — agent pipeline (includes roadmap refresh note)
- [`docs/0020-rate-limiting-production.md`](docs/0020-rate-limiting-production.md) — rate limits (implementation guide; not duplicated here)
