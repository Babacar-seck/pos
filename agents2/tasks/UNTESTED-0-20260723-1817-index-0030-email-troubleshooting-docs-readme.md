# Index 0030 reservation email troubleshooting in docs/README

## GitHub Issues
- **Issue:** (none — enhancement reviewer)
- **0**

## Problem / goal

**`docs/0030-reservation-confirmation-email-troubleshooting.md`** is the live ops runbook for “booking has email but no confirmation,” but **`docs/README.md`** never lists it under Email & SMTP (or elsewhere). Operators following the docs index stop at **0005** / **0056** and miss the diagnose script + Settings SMTP checklist. Sibling **`NEW-0-20260723-0658-refresh-0030-…`** owns a light body refresh and only *confirms* an index entry *if it exists* — it does not add one.

## Evidence (008 preflight / review)

- Weekly sweep 2026-07-23T18:16Z: `SIGNAL docs_stale×14` + `changelog_sparse` already owned; `demo_tables_check=ok`; Unreleased=1 post-2.1.28; NEW backlog≈85
- `rg` on **`docs/README.md`**: no hits for `0030` / `reservation-confirmation-email`
- File on disk: **`docs/0030-reservation-confirmation-email-troubleshooting.md`** (age >90d; cross-linked from email NEWs)
- Do **not** merge with **0658** refresh (body/commands) or gmail **0018** align NEW

## High-level instructions for coder

- In **`docs/README.md` Email & SMTP**, add one row for **`0030-reservation-confirmation-email-troubleshooting.md`**: confirmation not arriving, `diagnose_reservation_email.py`, Settings → Email SMTP checks
- Index only; no product code; no bulk rewrite of 0030 (leave body to **0658** if still open)
- Pass/fail: `rg -n '0030|confirmation-email-troubleshooting' docs/README.md` hits Email & SMTP; link resolves

## Coder notes

- On start (2026-07-26): goal already satisfied on `development`. Sibling **`CLOSED-0-20260723-0658-refresh-0030-…`** (release 2.1.100 / commit `735ea616`) indexed **0030** under **Email & SMTP** and **Quick links** while refreshing the runbook body.
- Verified current `docs/README.md`:
  - L17 Quick links: “Troubleshoot missing reservation confirmation email” → `0030-…`
  - L43 Email & SMTP: row with diagnose script / tenant vs global SMTP blurb
- Target file `docs/0030-reservation-confirmation-email-troubleshooting.md` exists; no further README edit needed; no `back/` / `front/` changes.

## Testing instructions

### What to verify

- `docs/README.md` lists **0030** under **Email & SMTP** (and optionally Quick links).
- The markdown link resolves to the on-disk runbook.

### How to test

```bash
# From repo root
rg -n '0030|confirmation-email-troubleshooting' docs/README.md
test -f docs/0030-reservation-confirmation-email-troubleshooting.md && echo OK
```

### Pass/fail criteria

- **Pass:** `rg` hits Email & SMTP (and Quick links); `docs/0030-reservation-confirmation-email-troubleshooting.md` exists; no product code required for this task.
- **Fail:** 0030 missing from Email & SMTP table, or link target missing.
