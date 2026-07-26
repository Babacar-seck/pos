# Mark 0024 deploy CSS fix as shipped

## GitHub Issues
- **Issue:** (none — enhancement reviewer)
- **0**

## Problem / goal

`docs/0057-deploy-css-fix-amvara9.md` still reads like an open incident (“what to change for your confirmation”) while both recommended fixes are already in the repo. Operators and agents may re-open a solved deploy CSS stale-build issue.

## Evidence (008 preflight / review)

- Doc age >90d; not in the 14 SIGNAL basename list but still stale alongside other `docs/*.md`
- `scripts/deploy-amvara9.sh` already runs `docker compose … build --no-cache front`
- `front/nginx.conf` already sets `Cache-Control: no-cache, no-store, must-revalidate` on the SPA `index.html` location
- No existing `agents2/tasks/*` covers **0024-deploy** (WhatsApp notes use a different `0024-whatsapp-*` file)

## High-level instructions for coder

- Add a short **Status (shipped)** banner at the top of `docs/0057-deploy-css-fix-amvara9.md`: front `--no-cache` deploy build + `index.html` no-cache headers are in place; keep the root-cause narrative as historical context.
- Point to current paths (`scripts/deploy-amvara9.sh`, `front/nginx.conf`) instead of “proposed” diff language.
- Do **not** rewrite the whole doc or change deploy behaviour unless a real regression is found.
- Pass criteria: doc opens with shipped status; no contradictory “please confirm these changes” framing; `docs/README.md` index blurb optional one-line update if it still implies an open fix.

## Implementation notes (coder)

- Confirmed in repo: `scripts/deploy-amvara9.sh` removes existing front image then `build --no-cache front`; `front/nginx.conf` `location /` has `Cache-Control: no-cache, no-store, must-revalidate`; compose uses `up -d` (not relying on `up --build` alone for front).
- Updated `docs/0057-deploy-css-fix-amvara9.md`: **Status (shipped)** banner; reframed problem/root-cause as historical; replaced “What to change (for your confirmation)” with “What was changed (now in repo)”; summary table marks items shipped.
- Updated `docs/README.md` deployment index line for 0057 to say **Shipped** + historical notes.
- No product/deploy script changes.

## Testing instructions

### What to verify

1. `docs/0057-deploy-css-fix-amvara9.md` opens with a **Status (shipped)** statement naming `scripts/deploy-amvara9.sh` (`--no-cache` front) and `front/nginx.conf` (SPA document no-cache headers).
2. The doc no longer asks for confirmation of proposed changes (“for your confirmation” / “After applying…” as open work).
3. `docs/README.md` deployment table describes 0057 as shipped (not an open fix).
4. Repo still matches the banner claims (spot-check only; no deploy required for this docs task).

### How to test

```bash
# From repo root
head -n 20 docs/0057-deploy-css-fix-amvara9.md
grep -n '0057-deploy-css' docs/README.md
grep -n 'build --no-cache front' scripts/deploy-amvara9.sh
grep -n 'no-cache, no-store, must-revalidate' front/nginx.conf
```

Optional: confirm no remaining open-incident framing:

```bash
grep -nE 'for your confirmation|After applying \(1\) and \(2\)|What to change' docs/0057-deploy-css-fix-amvara9.md || true
```

(Expect no matches for those open-work phrases.)

### Pass/fail criteria

- **Pass:** First screenful of 0057 says shipped; README index says shipped; grep confirms deploy script + nginx still implement the fix; no “please confirm these changes” framing.
- **Fail:** Doc still reads as an open incident, README still implies an unfixed deploy CSS issue, or banner claims disagree with `deploy-amvara9.sh` / `front/nginx.conf`.
