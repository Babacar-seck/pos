# Mark deploy-via-images plan (0029) as deferred

## GitHub Issues
- **Issue:** (none — enhancement reviewer)
- **0**

## Problem / goal

**`docs/0029-deployment-images-plan-next-month.md`** and its **`docs/README.md`** index row still say **“Todo (next month)”** from March 2026. Production deploy on amvara9 remains build-on-server (see **0001** / **0004**); the “next month” window has passed, so the index misleads operators into thinking image/registry deploy is imminent.

## Evidence (008 preflight / review)

- `SIGNAL docs_stale` — **`docs/0029-deployment-images-plan-next-month.md`** untouched >90d
- `docs/README.md` Plans table: “**Todo (next month):** Deploy via images…”
- 0029 header: **Status: Todo plan (next month)**; related live ops docs (**0001**, **0004**) still describe current compose/build deploy

## High-level instructions for coder

- Status-only edit: set 0029 header (and README index blurb) to **Deferred / not scheduled** (or equivalent), noting current deploy path remains documented in **0001** / **0004**
- Do **not** implement registry/two-slot deploy in this task; do not rewrite the plan body
- Pass criteria: docs index no longer claims “next month”; reader is pointed at current deploy docs

## Implementation notes (coder)

- `docs/0029-deployment-images-plan-next-month.md`: status → **Deferred / not scheduled**; added **Current deploy path** line pointing at **0001** / **0004**; title softened to “deferred plan”. Plan body left unchanged.
- `docs/README.md` Deployment table row: **Deferred / not scheduled** + links to current deploy docs. No product code.

## Testing instructions

### What to verify

Docs no longer present image/registry deploy as an imminent “next month” todo; readers are pointed at the live amvara9 deploy path.

### How to test

```bash
# From repo root
rg -n 'Todo \(next month\)|Todo plan \(next month\)' docs/README.md docs/0029-deployment-images-plan-next-month.md
# Expect: no matches in header / README index (body checklist heading may still say “next month”)

rg -n 'Deferred / not scheduled' docs/README.md docs/0029-deployment-images-plan-next-month.md
# Expect: hits in both files

# Links resolve (files exist)
test -f docs/0001-ci-cd-amvara9.md && test -f docs/0004-deployment.md && echo OK
```

### Pass/fail criteria

- **Pass:** README 0029 row and 0029 header say deferred/not scheduled; both point at **0001** / **0004**; no registry/two-slot implementation; plan body not rewritten.
- **Fail:** Index still says “Todo (next month)” as the status, or product/deploy scripts were changed.
