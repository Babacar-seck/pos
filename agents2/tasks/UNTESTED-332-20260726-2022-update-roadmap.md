# Update roadmap

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/332
- **332**

## Problem / goal

Root **`ROADMAP.md`** is hard to use: long mixed completed/missing lists, rate-limiting strategy drafts still inline, and it lags the 2026-07-26 shipped slices (TSE, printing, split bill, offline cash, warehouses, import, promos, branch hub, birthday guest, guest feedback / VeriFactu, club loyalty, pricing, and related archives under `agents2/tasks/done/2026/07/26/`). Owner wants it **meaningful** and treated as a **recurring** maintenance task so agents do not need a manual reminder.

Cross-check: **`CHANGELOG.md`**, **`docs/0032-github-issues-roadmap.md`**, **`docs/README.md`**, and today’s CLOSED task summaries.

## High-level instructions for coder

- Rewrite **`ROADMAP.md`** into a short, scannable source of truth: clear **Shipped**, **In progress / next**, and **Deferred** sections (or equivalent). Prefer links to `docs/` and issue numbers over essay-length bullets.
- Sync completed items with what actually shipped (especially 2026-07-26 work and recent Delivery / waitlist / groups / SaaS / platform items already partially listed). Remove or relocate obsolete “strategy draft” blobs (e.g. long rate-limit howto) into the matching doc if still useful — keep ROADMAP as status, not a second implementation guide.
- Fix stale “Missing” rows that are now shipped (e.g. multi-warehouse / split-bill / offline cash MVP slices if still implied only under umbrella #52).
- Make refresh **recurring**: document a lightweight cadence (e.g. after each batch of CLOSED product issues, or weekly with **008** enhancement reviewer) in ROADMAP itself and/or a one-line note in `docs/agent-loop.md` / `docs/0032-github-issues-roadmap.md` — do not invent a new agent role unless needed.
- Do **not** paste secrets, env, or raw logs into the roadmap or this task.
- Append **Testing instructions** (docs-only checks: structure, no stale “missing” for today’s CLOSED features, links resolve).

## Implementation summary

- Rewrote root **`ROADMAP.md`**: Shipped / In progress / Deferred tables + recurring refresh section; removed ~300 lines of rate-limit strategy draft (still covered by `docs/0020`).
- Updated **`docs/0032-github-issues-roadmap.md`** #52 table: split bill, join tables, promos, birthdays statuses match 2026-07-26 CLOSED work.
- Cadence notes in **`ROADMAP.md`**, **`docs/agent-loop.md`**, **`agents2/008-enhancement-reviewer.md`**, and **`docs/README.md`** (0032 blurb).
- **`CHANGELOG.md`** `[Unreleased]` Changed entry for #332.

## Testing instructions

Docs-only verification (no app restart required):

1. **Structure:** Open `ROADMAP.md`. Confirm sections exist in order: **How to keep this current**, **Shipped**, **In progress / next**, **Deferred**, **Related**. Confirm there is **no** long “Recommended Rate Limiting Strategy” / env-var checklist blob (rate limits belong in `docs/0020-rate-limiting-production.md`).
2. **No stale missing for 2026-07-26 CLOSED features:** In `ROADMAP.md` Shipped table and `docs/0032-github-issues-roadmap.md` #52 table, confirm these are **not** listed as Not started / Missing: multi-warehouse (#320), split bill (#318/#331), offline cash MVP (#319), CSV migration (#321), price promos (#322), branch hub (#323), guest birthdays (#324), guest feedback (#325), VeriFactu prep (#326), club loyalty (#327), hardware printing (#317), TSE Phase 1 (#316), floor-plan table join (`docs/0051`).
3. **Links resolve:** From repo root, confirm these paths exist: `docs/0032-github-issues-roadmap.md`, `docs/0020-rate-limiting-production.md`, `docs/0071-split-bill.md`, `docs/0068-price-promotions.md`, `docs/0051-table-groups-mvp.md`, `docs/0066-club-loyalty.md`, `docs/agent-loop.md`, `CHANGELOG.md`.
4. **Recurring cadence:** `ROADMAP.md` “How to keep this current” mentions CLOSED batches and agent **008**; `docs/agent-loop.md` Related section links `ROADMAP.md`; `agents2/008-enhancement-reviewer.md` “Docs vs code” mentions roadmap drift → queue `FEAT-0-…-update-roadmap.md`.
5. **Changelog:** `CHANGELOG.md` `[Unreleased]` → Changed contains a Roadmap (#332) line.
