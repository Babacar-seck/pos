# Crunch stale branches

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/314
- **314**

## Problem / goal

Clean up stale git branches. Keep **`development`** and **`master`** (production). Remove obsolete local and remote feature/enhancement branches that are fully merged or no longer needed so the remote stays lean and agents do not confuse active work with dead tips.

At planning time (**2026-07-26** UTC), remote tips include several merged-into-`development` branches (e.g. `feat/*`, `enh/order-flow`, `feature/table-reservations`, security/style branches) plus a few not-merged remotes (`gilberto-dev`, `feature/i18n-support-…`, `rbac-implementation-…`) that need an explicit keep-or-delete decision.

See **`.cursor/rules/git-development-branch-workflow.mdc`**, **`AGENTS.md`** (routine work on **`development`**; **`master`** for production).

## High-level instructions for coder

- Sync **`development`** (`./scripts/git-sync-development.sh`). Do **not** delete **`development`**, **`master`**, or **`origin/HEAD`**.
- Inventory local and remote branches; classify each as: already merged into **`development`** (safe delete), already merged into **`master`**, or **not merged** (needs human judgment / leave unless clearly abandoned).
- Delete **merged** remote branches with `git push origin --delete <branch>` (no force-push to **`master`** / **`development`**). Prune local tracking refs (`git fetch --prune`) and delete matching local branches if present.
- For **unmerged** remotes: do **not** mass-delete. Either leave them with a short note in the task, or confirm they are abandoned before deleting. Prefer documenting the list over risky deletion.
- Never rewrite history on **`development`** or **`master`**. No `--force` / `--force-with-lease` on those branches.
- Append **Testing instructions** listing deleted vs retained branches and commands used so the tester can verify remotes.

## Implementation notes (coder)

Synced **`development`**, inventoried with `git branch -r --merged/--no-merged`, deleted only tips already ancestor of **`origin/development`**. No force-push; **`development`** / **`master`** untouched.

### Already gone on remote (pruned at start)

These remotes were already deleted upstream before this run; `git fetch --prune` dropped the stale tracking refs:

- `origin/enh/order-flow`
- `origin/feat/docker-compose-all-in`
- `origin/feat/languages`
- `origin/feat/products-and-provider`
- `origin/feature/table-reservations`

### Deleted remote (this run)

Confirmed `git merge-base --is-ancestor` into **`origin/development`**, then:

```bash
git push origin --delete \
  feat/ariba-doner-marketing-site \
  security-fixes-payment-session-7273677154460226940 \
  style-standardization-translations
```

### Deleted local (this run)

Also fully merged into **`origin/development`**:

```bash
git branch -d feat/docker-compose-all-in feat/languages feature/table-reservations
```

### Retained (protected)

- `development` / `origin/development`
- `master` / `origin/master`
- `origin/HEAD` → `origin/master`

### Retained (unmerged — do not mass-delete)

Left in place pending human keep-or-delete:

| Branch | Tip (approx) | Notes |
|--------|--------------|--------|
| `origin/feature/i18n-support-15334820750941838496` | 2026-01-16 — i18n complete | Not ancestor of `development` |
| `origin/gilberto-dev` | 2026-06-04 — events guest list / RSVP / QR | Not ancestor of `development` |
| `origin/rbac-implementation-1959159120742286807` | 2026-01-19 — custom RBAC | Not ancestor of `development` |

## Testing instructions

1. From repo root: `git fetch --prune origin`
2. Confirm protected remotes exist:
   ```bash
   git rev-parse origin/development origin/master
   ```
3. Confirm deleted remotes are gone (each should fail / empty):
   ```bash
   git show-ref --verify refs/remotes/origin/feat/ariba-doner-marketing-site
   git show-ref --verify refs/remotes/origin/security-fixes-payment-session-7273677154460226940
   git show-ref --verify refs/remotes/origin/style-standardization-translations
   ```
4. Confirm unmerged remotes still present:
   ```bash
   git branch -r | grep -E 'i18n-support|gilberto-dev|rbac-implementation'
   ```
5. Optional: `git branch -r --merged origin/development` should only list `origin/development` (plus any new tips since this run). Local branches should be only `development` and `master` on the coder machine after cleanup.
6. Confirm **no** force-push / history rewrite on `development` or `master`.
