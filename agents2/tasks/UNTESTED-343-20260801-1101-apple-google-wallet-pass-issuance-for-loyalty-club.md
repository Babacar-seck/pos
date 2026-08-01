# Apple/Google Wallet pass issuance for Loyalty Club

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/343
- **343**

## Problem / goal

Loyalty Club points/stamps, VIP tiers, and referrals are shipped (`docs/0066-club-loyalty.md`, #327/#334/#337), but **wallet pass issuance** is still stubbed: `wallet_pass_status()` reports Apple/Google unavailable until signing certs / issuer accounts are configured. Goal is real PassKit `.pkpass` + Google Wallet loyalty objects on join, with balance push-updates, so Satisfecho can close the gap versus bolt-on wallet-pass tools.

## High-level instructions for coder

- Read **`docs/0066-club-loyalty.md`** (wallet / `wallet_pass_status()` sections) and the existing stub paths; extend issuance rather than inventing a second loyalty join flow.
- **Apple Wallet:** wire signed `.pkpass` generation (Pass Type ID + WWDR) on customer join; implement PassKit web-service push-update when balance changes (update, not reissue).
- **Google Wallet:** wire issuer/service-account loyalty object create on join; PATCH object for balance updates.
- **Config:** decide shared platform cert/issuer vs per-tenant onboarding (document Apple multi-merchant Pass Type ID constraints before assuming shared); per-tenant enablement with clear fallback to balance-view-only when certs missing.
- **Docs / marketing:** update 0066 with setup steps and live `wallet_pass_status()` behavior; when ready, align pricing/features copy (#328) so wallet passes are described accurately — no premature “live” claims before certs work.
- Prefer an incremental vertical slice (one platform or status+fallback first) if full dual-platform MVP is blocked on Apple/Google account approval; note operational blockers in the task file.
- **Out of scope:** reworking earn/redeem/VIP/referral rules already shipped; staff Factura CRM; inventing a second public loyalty URL.
- Pass criteria (MVP): join yields working Apple + Google passes when configured; balance changes push updates on both; graceful fallback without certs; 0066 updated; pytest/smoke for generate + update-push happy paths.
- Append **Testing instructions** when moving to UNTESTED.

## Security note (001)

Issue body summarized for product intent only; no secrets, certs, or credentials copied.

## Implementation notes (feature coder)

- Shared platform Apple Pass Type ID + Google issuer via env; per-tenant `wallet_passes_enabled` opt-out.
- Module: `back/app/loyalty_wallet.py`; migration `20260801131339_loyalty_wallet_passes.sql`.
- Apple `.pkpass` signed with `openssl smime` (SHA-1 PKCS#7); PassKit web service under `/public/passkit/v1/…`.
- Google loyalty class/object + JWT save URL; PATCH on ledger changes.
- APNs push optional (`LOYALTY_APPLE_APNS_*`); without it, tag still bumps and devices can refresh via web service after a push or re-open.
- **Operational blocker:** real Apple Developer Pass Type ID certs + Google Wallet issuer approval still required in each environment before production devices accept passes. Pytest uses ephemeral self-signed certs + mocked Google HTTP.
- Pricing/features marketing copy (#328) left unchanged — do not claim “live” wallet passes until ops certs are verified.

## Testing instructions

1. **Migrate:** `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python -m app.migrate` — expect schema including `loyalty_apple_device` / wallet columns (`20260801131339`).
2. **Pytest (wallet):** `docker compose … exec back python3 -m pytest tests/test_loyalty_wallet.py -q` — expect 5 passed (pkpass ZIP, Google create/PATCH mocked, PassKit register + balance update, tenant disable → 503).
3. **Pytest (regression):** `… pytest tests/test_club_loyalty.py -q` — including `test_wallet_status_unconfigured` still reports unavailable without env certs.
4. **Unconfigured fallback:** With no `LOYALTY_APPLE_*` / `LOYALTY_GOOGLE_*` files: enable loyalty for tenant 1, join via `/loyalty/1`, confirm success + balance card link and no Add-to-Wallet buttons (or only detail note).
5. **Configured happy path (optional if certs present):** Set env paths to real or test PEMs + Google SA JSON, restart back, join → `GET /public/loyalty/members/{token}/wallet` shows `*_available: true`; download `…/wallet/apple.pkpass` (`Content-Type: application/vnd.apple.pkpass`); `GET …/wallet/google` returns `google_save_url`. Adjust membership balance → Google PATCH attempted; with a registered PassKit device, APNs called when APNs key set.
6. **Staff toggle:** Settings → Loyalty → uncheck “Offer Apple / Google Wallet passes”, save; wallet status for that tenant becomes unavailable while join still works.
7. **Front:** `python3 scripts/check-i18n-locale-parity.py` PASS; `BASE_URL=http://127.0.0.1:4202 npm run test:landing-version --prefix front` PASS; no Angular compile errors in `docker logs --since 10m pos-front`.
8. **Docs:** Spot-check `docs/0066-club-loyalty.md` wallet setup + `wallet_pass_status()` table.
