# Preflight: skip demo_tables_check SIGNAL when repair task is already queued

## GitHub Issues
- **Issue:** (none — enhancement reviewer)
- **0**

## Problem / goal

Preflight always emits `SIGNAL demo_tables_check=fail` when `check_demo_tables` exits non-zero. When an open root task already owns demo-table repair, every agent-loop tick re-wakes **008** on the same owned failure. (Historical owner **`NEW-0-20260712-1614-repair-demo-tables-t01-t10`** was superseded by **#305** / **`CLOSED-305-20260723-0621-missing-tables.md`** and archived under `done/2026/07/12/` — do not cite that NEW as live owner.) Mirror the queued-docs skip pattern: keep the check output visible, but do not count an owned fail as a wake SIGNAL.

## Evidence (008 preflight / review)

- Digest: `SIGNAL demo_tables_check=fail (run seed_demo_tables)` every run
- Re-check 2026-07-22T21:20Z: still Missing `T05`/`T07`/`T10`, Wrong `T08` seats (expected 2, got 6) — unchanged; root cause documented on the repair NEW (`run()` skips partial tenants)
- Sibling: **`NEW-0-20260722-1433-preflight-skip-queued-stale-docs.md`** already covers `docs_stale` ownership; demo has no equivalent
- Demo-table product repair shipped as **CLOSED-305** (`done/2026/07/23/CLOSED-305-20260723-0621-missing-tables.md`). On a future `check_demo_tables` fail, ownership is whichever open root `{NEW,FEAT,WIP,UNTESTED,TESTING}-*.md` covers demo-table repair (or a new NEW if none). Demo products: historical **`NEW-0-20260722-1320-repair-demo-products-partial-tenant.md`** (may already be archived).

## High-level instructions for coder

- In `scripts/enhancement-reviewer-preflight.sh`, after a failing `check_demo_tables`, **skip** `SIGNAL demo_tables_check=fail` / `G008_DEMO_SIGNALS` increment if any root `agents2/tasks/{NEW,FEAT,WIP,UNTESTED,TESTING}-*.md` already covers demo-table repair (filename or body mentions `check_demo_tables`, `seed_demo_tables`, or `repair-demo-tables`)
- Still print a non-SIGNAL line such as `demo_tables_check=fail (owned by open task …)` so humans see the health status
- If no open owner exists, keep today’s SIGNAL behaviour (e.g. after CLOSED-305 with no new repair NEW, a fresh fail must SIGNAL)
- Do not implement the seed repair in this task; do not revive the archived 20260712 repair NEW
- Pass criteria: with an open repair-owner task present, readonly preflight shows fail as informational and does not increment `G008_DEMO_SIGNALS` / wake-only SIGNAL count for that fail; removing/renaming the owner restores SIGNAL
