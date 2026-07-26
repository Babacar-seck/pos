# Prioritisation: Docs 0019–0022 (What to Do First)

Short reference for the development plans in docs 0019–0022 and suggested order.

**Status (2026-07):** Working plan (**0021**) is **shipped**. The next open item in this set is **0022 (OAuth)** — design notes only; not implemented. See **[0022-oauth-social-login-notes.md](0022-oauth-social-login-notes.md)**.

---

## Status of each doc

| Doc | Topic | Status | Action |
|-----|--------|--------|--------|
| **0019** | No-show (reservations) | **Done** | None. Doc describes what was implemented (status `no_show`, reminder email, UI). |
| **0020** | Rate limiting | **Mostly done** | Core is in place (global, login, register, payment). Optional: public menu limits, file upload limits (see ROADMAP checklist). |
| **0021** | Working plan (kitchen, bar, waiters) | **Done** | Implemented: shift table, CRUD API, `/working-plan` page, permissions, opening-hours alignment, personnel-per-shift in Settings, owner notification, time step (30 min / 1 h), “use any hour” (e.g. cleaning). Living guide: **[0021-working-plan.md](0021-working-plan.md)**. |
| **0022** | OAuth / social login (Google, Microsoft, etc.) | **To do** | Design done; implementation: nullable password, `user_oauth_account` table, provider endpoints, login buttons. Notes: **[0022-oauth-social-login-notes.md](0022-oauth-social-login-notes.md)**. |

---

## Recommendation: next open item is **0022 (OAuth)**

**0021 (Working plan) is completed background** — do not re-open it as “what to do first.” Ops live at `/working-plan`; see **0021-working-plan.md** and Puppeteer `test:working-plan`.

### Why OAuth next (when product prioritises auth)

1. **Only unfinished item in 0019–0022** – 0019 and 0021 are done; 0020 core is in place.
2. **Design already captured** – Follow **[0022-oauth-social-login-notes.md](0022-oauth-social-login-notes.md)** (nullable password, `user_oauth_account`, provider endpoints, login buttons). Do not invent a parallel OAuth plan from this prioritisation doc alone.
3. **Security-sensitive** – Nullable password, new table, multiple providers; deserves a dedicated pass and review when scheduled.
4. **Incremental** – Roll out Google first, then Microsoft, then others as needed.

### Optional: 0020 follow-ups (hardening, not blocking OAuth)

These are incremental hardening and do **not** block starting OAuth:

- Public menu rate limits (e.g. 30/min per IP).
- File upload rate limits (e.g. 10/hour per user).

See **[0020-rate-limiting-production.md](0020-rate-limiting-production.md)** / ROADMAP checklist.

---

## Suggested order (summary)

1. **0019 / 0021 –** Done; no further work from this prioritisation set.  
2. **0022 – OAuth** (next open item; Google, then Microsoft, then GitHub/Facebook as needed) — design: **0022-oauth-social-login-notes.md**.  
3. **0020 –** Optional extra rate limits (public menu, uploads); hardening only.  
