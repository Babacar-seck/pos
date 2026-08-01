# Certified middleware to unblock VeriFactu + TSE live mode

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/342
- **342**

## Problem / goal

VeriFactu (Spain) and TSE (Germany) are functionally complete in **test/stub** mode but **`live` is gated** on certified middleware that is not wired yet (`docs/0065-verifactu-production.md`, `docs/0072-tse-fiscal-compliance.md`; ROADMAP “In progress / next”). Goal: decide build-vs-buy, integrate certified providers so `fiscal_mode: live` / TSE `live` work for real tenants, and keep marketing/docs honest until then.

## High-level instructions for coder

- Read **`docs/0065-verifactu-production.md`**, **`docs/0072-tse-fiscal-compliance.md`**, and the ROADMAP live-gate row; reuse existing issue/cancel and TSE auto-sign paths — swap stub for provider calls in `live` only.
- **Decision record:** publish an ADR comparing ≥2 certified options per regime (e.g. Fiskaly / Verifacti / Efsta for VeriFactu; certified TSE cloud/hardware for Germany) — cost, API shape, certification coverage, effort — and pick one per regime before deep coding.
- **VeriFactu:** wire chosen provider into issue/cancel so `live` submits via the provider (AEAT protocol/cert upkeep on their side).
- **TSE:** wire chosen certified module into the existing auto-sign path so `live` yields a real signed receipt, not the stub signature.
- **Guards:** prevent enabling `live` until provider integration is verified; document credential/cert renewal cadence.
- **Docs / product copy:** update 0065, 0072, and ROADMAP once unblocked; review `/pricing` and `/features` so nothing claims “certified” / “live-ready” before this ships.
- Prefer ADR + one-regime vertical slice if dual-regime full live is too large for one WIP; note legal/ops blockers without inventing credentials in-repo.
- **Out of scope:** rewriting sandbox/test paths that already work; representing either feature as certified in marketing before providers are live; committing AEAT/TSE secrets into the repo (use `config.env` / deploy secrets).
- Pass criteria (MVP): ADR with chosen providers; VeriFactu `live` issues a real AEAT-submitted invoice for a test tenant; TSE `live` produces a certified-module-signed receipt for a test tenant; live-enable guard; docs + ROADMAP updated; pricing/features reviewed for premature claims.
- Append **Testing instructions** when moving to UNTESTED.

## Security note (001)

Issue body summarized for product intent only; no secrets or credentials copied.

## Implementation summary (010)

- ADR: **`docs/0074-fiscal-certified-middleware.md`** — pick **Fiskaly SIGN ES** (VeriFactu) and **Fiskaly SIGN DE** (TSE); Verifacti / Epson-Swissbit as runners-up; `generic` + non-prod `mock` retained.
- Adapters: `back/app/fiscal_providers.py`, `back/app/tse_providers.py`; wired into issue/cancel and TSE sale/storno.
- Live guards: unlock + `live_credentials_ready()`; mock forbidden when `PRODUCTION=true`; live failures → **502** (no stub-only success).
- Docs: 0065, 0072, ROADMAP, README, `config.env.example`, CHANGELOG; `/features` + Settings `en.json` honesty review (no premature certified claims). `/pricing` has no fiscal/TSE certified claims.
- **Ops blocker:** real AEAT/BSI production remisión needs commercial Fiskaly credentials (not in repo). CI vertical slice uses `mock`.

## Testing instructions

### Automated (Docker)

```bash
# From repo root, stack up
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T back \
  python3 -m pytest tests/test_fiscal_invoice_api.py tests/test_tse_api.py -q
```

Expect **17 passed**, including:

- `test_live_mode_blocked_without_unlock` / `test_live_mode_gated`
- `test_live_issue_with_mock_middleware` (VeriFactu live → `submission_status=mock_accepted`)
- `test_live_sign_with_mock_provider` (TSE live → `mock-sig-*` / `MOCK-TSE-*`)

### Manual / smoke

1. Confirm app responds: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:4202/` → **200**.
2. `/features` and Settings → Payments: copy still says preparation / locked live (mentions Fiskaly when unlocked path exists) — **not** “AEAT certified” / “BSI certified”.
3. Without unlock: Settings cannot set `fiscal_mode` or `tse_mode` to `live` (400).
4. Optional non-prod vertical slice: set `FISCAL_MIDDLEWARE_PROVIDER=mock`, `FISCAL_LIVE_UNLOCK=true` (and TSE equivalents), restart back, set tenant live, issue fiscal invoice / pay with TSE — expect accepted mock submission statuses. **Do not** enable mock on production.

### Ops note for real LIVE

Configure Fiskaly TEST keys (`FISCAL_MIDDLEWARE_PROVIDER=fiskaly_sign_es`, `TSE_PROVIDER=fiskaly_sign_de`, secrets via `config.env`), verify against Fiskaly TEST, then unlock LIVE only after sign-off. See `docs/0074-fiscal-certified-middleware.md` renewal cadence.
