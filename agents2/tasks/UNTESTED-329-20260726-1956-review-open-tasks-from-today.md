# Review open tasks from today

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/329
- **329**

## Problem / goal

Meta ask after a busy day of product issues: confirm what (if anything) is still open in GitHub and in the agent task queue, and close the loop so nothing is left untracked.

**001 inventory (UTC 2026-07-26 ~19:56):**
- Open GitHub issues: only **#329** (this issue).
- `agents2/tasks/` root: empty of `FEAT-` / `NEW-` / `WIP-` / `UNTESTED-` / `TESTING-` (queue clear aside from this new FEAT).
- Today’s product issues **#311–#328** are **CLOSED** with matching `CLOSED-*` archives under `agents2/tasks/done/2026/07/26/` (loyalty **#327** includes the SlowAPI public-500 fix already verified).
- Docker digest heuristics (loyalty 500s, mid-day Angular bundle failures) are **not standing**: live `GET /api/public/tenants/1/loyalty` → 200; front last rebuild succeeded; landing → 200. No `NEW-` filed from logs this run.

## High-level instructions for coder

- Treat this as a **status / close-out** task, not new product code in `back/` / `front/` unless a real residual gap appears during the check.
- Re-check open GitHub issues (`gh issue list --repo satisfecho/pos --state open`) and open files under `agents2/tasks/` (exclude `done/`).
- Confirm today’s closed work is archived under `agents2/tasks/done/2026/07/26/` for the issues listed above; note any CLOSED GH issue missing a task archive (or vice versa) without inventing secrets or pasting log blobs.
- If the queue is still empty of real product work: comment on **#329** with the short inventory, then **close #329**.
- If you find a real unfinished product gap, open a focused follow-up GitHub issue (or FEAT/NEW via 001 conventions) — do not pile unrelated work into #329.
- Append **Testing instructions** only if any code/docs change was required; otherwise a short verification note (issue closed + queues empty) is enough for the tester/closer.

## Implementation notes (010 feature coder, UTC 2026-07-26)

Status / close-out only — **no** `back/` / `front/` / docs product changes.

**Re-check:**
- Open GitHub issues: only **#329** (this meta issue).
- `agents2/tasks/` live queue: only this task (no other `NEW` / `FEAT` / `WIP` / `UNTESTED` / `TESTING`).
- **#311–#328**: all **CLOSED** on GitHub; each has a matching `CLOSED-*` archive under `agents2/tasks/done/2026/07/26/` (18/18; no missing archive, no extra archive in that day folder).
- Live smoke: `GET http://127.0.0.1:4202/` → **200**; `GET /api/public/tenants/1/loyalty` → **200**.
- No residual product gap found → no follow-up issue filed.

**Actions:** `agent:wip` added; inventory commented on **#329**; **#329** closed.

## Testing instructions

No product code changed. Tester/closer should confirm:
1. `gh issue list --repo satisfecho/pos --state open` shows no open product issues (ideally empty after #329 closed).
2. `agents2/tasks/` has no leftover `NEW-` / `FEAT-` / `WIP-` product work (this file should be the only pipeline item until closed/archived).
3. `agents2/tasks/done/2026/07/26/` still contains `CLOSED-311` … `CLOSED-328` archives.
