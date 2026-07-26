# Index 0051 table-groups MVP in docs/README

## GitHub Issues
- **Issue:** (none — enhancement reviewer)
- **0**

## Problem / goal

**`docs/0051-table-groups-mvp.md`** documents floor-plan join/unjoin (combined seats, reservation pool) — distinct from restaurant multi-location groups (**0054**). It is on disk and referenced from closed join-UX work, but **`docs/README.md`** never lists it under Feature guides. Agents scanning the index can confuse **0054** restaurant groups with table groups, or miss the MVP doc entirely. Sibling **`NEW-0-20260722-1412-mark-0051-table-groups-shipped`** owns a shipped banner only — not a README row.

## Evidence (008 preflight / review)

- Weekly sweep 2026-07-23T18:24Z: `SIGNAL docs_stale×14` + `changelog_sparse` already owned; `demo_tables_check=ok`; NEW backlog≈88
- `rg` on **`docs/README.md`**: Feature guides has **0054** restaurant groups; no hits for `0051` / `table-groups`
- File on disk: **`docs/0051-table-groups-mvp.md`**
- Do **not** merge with **0054** Quick links / Feature guides NEWs (different feature)

## High-level instructions for coder

- In **`docs/README.md` Feature guides**, add one row for **`0051-table-groups-mvp.md`**: floor-plan table join/unjoin, combined seats, reservation pool (MVP; distinguish from **0054** restaurant groups)
- Index only; no product code; leave body/status banner to **1412** if still open
- Pass/fail: `rg -n '0051|table-groups-mvp' docs/README.md` under Feature guides; link resolves; blurb does not conflate with 0054

## Implementation notes (coder)

- Added Feature guides row for **`0051-table-groups-mvp.md`** (before **0052**): floor-plan join/unjoin MVP; blurb explicitly not restaurant multi-location groups (**0054**).
- Index only; no product code; sibling **1412** still owns shipped-banner work.

## Testing instructions

### What to verify
- **`docs/README.md`** Feature guides lists **`0051-table-groups-mvp.md`**.
- Link target exists; description distinguishes floor-plan table groups from **0054** restaurant groups.

### How to test
```bash
# From repo root
rg -n '0051|table-groups-mvp' docs/README.md
test -f docs/0051-table-groups-mvp.md
rg -n '0054-restaurant-groups' docs/README.md
```

### Pass/fail criteria
- **Pass:** `rg` hits the Feature guides row for `0051-table-groups-mvp`; file exists; blurb mentions floor-plan join/unjoin (or combined seats / reservation pool) and does not describe multi-location restaurant groups as the same feature as 0051.
- **Fail:** No Feature guides hit for 0051, broken link, or blurb conflates 0051 with 0054.
