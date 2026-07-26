# Mark 0008 order-management spec as shipped design

## GitHub Issues
- **Issue:** (none — enhancement reviewer)
- **0**

## Problem / goal

`docs/0008-order-management-logic.md` is a large design/spec (session-scoped orders, lifecycle, edge cases) with no status banner. Core behaviour (`session_id` on orders, per-browser isolation) has shipped. Alongside historical **`docs/0007-…`**, agents may treat the whole file as unfinished work or re-implement from the problem statement.

## Evidence (008 preflight / review)

- `SIGNAL docs_stale` continuation — **>90d**, deferred by earlier 2026-07-22 008 sweeps; not covered by a dedicated NEW (0007 historical NEW only references 0008)
- Code: `Order.session_id` / session checks in `back/app/main.py`; item `added_by_session` in models
- `docs/README.md` lists 0008 as live “lifecycle, session rules…” without shipped/design-history cue

## High-level instructions for coder

- Add a short top banner: **shipped core / design reference** — do not re-open the original “shared unpaid order” problem as backlog; treat remaining edge-case sections as reference, not a todo list. Point readers to current code/tests for behaviour.
- Optionally one-line README index tweak (“design reference / shipped session rules”).
- Do **not** bulk-rewrite or renumber the ~1.4k-line spec in this task.
- Pass/fail: banner (and optional README line) clear; no product code changes.

## Implementation notes (coder)

- Added **Status: shipped core / design reference** banner under the title in `docs/0008-order-management-logic.md` (session_id / added_by_session live; do not re-open shared-order backlog; edge cases = reference).
- Kept the #284 comments pointer in the banner block.
- Softened Problem Statement as historical framing; noted core `session_id` fix shipped.
- Updated `docs/README.md` 0008 index row to **shipped** session rules / design reference.
- No product code changes; no bulk rewrite of the ~1.4k-line body.

---

## Testing instructions

### What to verify

1. `docs/0008-order-management-logic.md` opens with a clear **shipped core / design reference** banner stating session-scoped orders are live and the shared-unpaid-order problem is not open backlog.
2. Remaining edge-case / proposed sections are unchanged (no bulk rewrite of the long body).
3. `docs/README.md` index row for 0008 says shipped / design reference (not an open backlog).
4. No changes under `back/` or `front/`.

### How to test

```bash
# From repo root
head -n 20 docs/0008-order-management-logic.md
rg -n "shipped core|design reference|session_id" docs/0008-order-management-logic.md | head
rg -n "0008-order-management" docs/README.md
git diff --stat -- back/ front/
git diff -- docs/0008-order-management-logic.md docs/README.md
```

Docs-only; no compose / Puppeteer required.

### Pass/fail criteria

| Criterion | Pass |
|-----------|------|
| Banner present in first screenful | Yes |
| Shared-order problem framed as historical / not backlog | Yes |
| README 0008 row has shipped / design-reference cue | Yes |
| No `back/` or `front/` diffs | Yes |
| Spec body not bulk-rewritten | Yes |
