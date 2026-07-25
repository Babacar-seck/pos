# Bump version, create release and promote to production

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/308
- **308**

## Problem / goal

Ship current tested work from **`development`** to **production** (amvara9 / satisfecho.de): ensure changelog/semver are release-ready, merge **`development` → `master`**, push **`master`** (triggers deploy), and publish a GitHub release if appropriate.

At planning time (**2026-07-25** UTC): **`front/package.json`** is **2.1.33**; **`CHANGELOG.md`** `[Unreleased]` is empty (latest cut **`## [2.1.33] - 2026-07-25`** SEO); **`origin/master`** tip is still the **2.1.27** promotion merge while **`origin/development`** is hundreds of commits ahead — production is behind. Issue body asks to promote to master and deploy; that is an explicit production request under **`.cursor/rules/git-development-branch-workflow.mdc`**.

See **`docs/0001-ci-cd-amvara9.md`**, **`docs/agent-loop.md`** (merge triggers), **`.cursor/rules/commit-changelog-version.mdc`**. Prior similar work: **#289** / **#256**.

## High-level instructions for coder

- Sync **`development`** (`./scripts/git-sync-development.sh`). Confirm local smoke: landing HTTP **200** on HAProxy port; `docker logs --since 10m pos-front` — no Angular build failures.
- **Changelog / version:** If `[Unreleased]` has material items since **2.1.33**, cut a new semver section, bump **`front/package.json`** + lockfile, run **`node front/scripts/get-commit-hash.js`**, and commit **`commit-hash.ts`** with the bump on **`development`**. If nothing unreleased remains, promote **2.1.33** (or the latest cut on **`development`**) — do not invent empty churn bumps.
- Merge **`development` → `master`** (fast-forward or merge commit) and **`git push origin master`**. Do not force-push.
- Monitor **Deploy to amvara9** (`.github/workflows/deploy-amvara9.yml`). If GHA SSH fails (known past failure mode), fall back to documented manual deploy via local **`ssh amvara9`** + **`scripts/deploy-amvara9.sh`**; do not claim success until production is updated.
- Publish a GitHub release tag matching the shipped semver with human-readable notes from the matching **`CHANGELOG.md`** section (not a raw agent dump).
- Post-deploy smoke on **https://www.satisfecho.de**: `/` and `/api/health` **200**; landing **app-version** / footer semver + short hash match the promoted commit; spot-check major shipped surfaces since **2.1.27** if time allows (delivery zones/track, SEO public pages, waitlist, etc.).
- This is **release/ops**, not feature coding — fix only blockers that prevent a safe promote; append **Testing instructions** with merge SHA, workflow run URL (or manual deploy evidence), release URL, and smoke results.

## Implementation notes (coder)

- No version bump: `[Unreleased]` empty; shipped **2.1.33** as cut on `development`.
- Merged `development` → `master` (`2b2505a4`) and pushed `master`.
- GitHub release **v2.1.33** published.
- GHA **Deploy to amvara9** run [30164265297](https://github.com/satisfecho/pos/actions/runs/30164265297) **failed** on marketing artifact fetch (expired Actions artifacts for antillana/dilruba/flamanapolitana/hakone; `MARKETING_VERIFY_NO_PLACEHOLDERS=1`).
- **Manual fallback:** `ssh amvara9` — backed up `front/sites`, `git reset --hard origin/master` to `2b2505a4`, restored marketing sites, ran `scripts/deploy-amvara9.sh` successfully.

## Testing instructions

1. Confirm **https://github.com/satisfecho/pos/releases/tag/v2.1.33** exists and points at the 2.1.33 release notes.
2. Confirm `origin/master` tip is merge **`2b2505a4`** (`Merge development: release through 2.1.33…`).
3. Production smoke (already run by coder; re-check):
   - `curl -sS -o /dev/null -w "%{http_code}\n" https://www.satisfecho.de/` → **200**
   - `curl -sS https://www.satisfecho.de/api/health` → `{"status":"ok"}` **200**
   - Landing meta `app-version` content **`2.1.33`**
   - Spot routes **200**: `/robots.txt`, `/sitemap.xml`, `/features`, `/waitlist/1`, `/delivery/1`, `/book/1`
4. On amvara9: `cd /development/pos && git rev-parse --short HEAD` → **`2b2505a4`**; `front/package.json` version **2.1.33**.
5. Note: GHA deploy remains red until marketing artifact PAT/expired-artifact issue is fixed; production was updated via manual deploy. Optional follow-up: re-publish marketing CI artifacts for dilruba/flamanapolitana/hakone/antillana or relax verify for expired artifacts.
