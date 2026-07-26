# Enhance guest feedback (survey + staff analytics)

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/325
- **325**

## Problem / goal

Baseline guest feedback already ships (`/feedback/:tenantId`, star rating, Google review deep-link; staff `/guest-feedback`). This issue extends that flow — not a rebuild — with richer surveys and staff-facing analytics (umbrella **#52** / `docs/0050-github-issue-52-split-plan.md` Issue 6; roadmap `docs/0032-github-issues-roadmap.md`). Google reviews remain deep-link only (no review-posting API).

## High-level instructions for coder

- Pick **one** MVP vertical beyond the baseline (prefer staff trend dashboard and/or CSV export over boiling the ocean). Optional NPS template and post-reservation email/SMS link are follow-ups if the first slice is thin.
- Extend existing public + staff feedback surfaces and APIs; respect rate limits in `docs/0020-rate-limiting-production.md` and branding on `/feedback/:tenantId` (`docs/0028-tenant-public-branding.md`).
- Receipt QR → feedback depends on the printing bridge — stub or document the link format if printing is not ready; do not block the whole MVP on hardware.
- Keep Google as deep-link only; do not attempt automated review submission.
- Cover with tests / existing Puppeteer smokes where useful (`test:guest-feedback-staff`, `test:feedback-public-i18n` in `docs/testing.md`); `CHANGELOG.md`; append **Testing instructions**.
- Tenant-scoped; no secrets or live guest PII in fixtures.

## Implementation notes (coder)

**MVP vertical shipped:** staff trends + CSV export (not NPS / email-SMS).

- **API:** `GET /tenant/guest-feedback/summary?days=` and `GET /tenant/guest-feedback/export` (`reservation:read`, admin rate limit).
- **UI:** `/guest-feedback` trends panel (30/90/365 lookback), star histogram, daily volume strip, Export CSV.
- **Docs:** `docs/0064-guest-feedback-analytics.md` (includes receipt QR URL format); updates to 0011, 0020, README, CHANGELOG, testing.md.
- **Follow-ups (out of scope):** NPS templates, post-reservation email/SMS, printer hardware embedding the QR.

## Testing instructions

1. **Backend unit tests** (Docker):
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T back \
     python3 -m pytest tests/test_guest_feedback.py -q
   ```
   Expect all tests green (includes summary aggregates + CSV tenant isolation).

2. **Staff Puppeteer smoke** (app on 4202, demo/staff credentials):
   ```bash
   BASE_URL=http://127.0.0.1:4202 HEADLESS=1 \
     LOGIN_EMAIL=… LOGIN_PASSWORD=… \
     npm run test:guest-feedback-staff --prefix front
   ```
   Expect: list + summary GET 200, analytics panel, Export CSV button, no raw `FEEDBACK.*` keys.

3. **Manual spot-check (optional):**
   - Open `/guest-feedback` → Trends shows counts; switch 30/90/365.
   - Click **Export CSV** → file downloads with header `id,created_at,rating,…`.
   - Confirm other tenants’ feedback does not appear (pytest covers this).
   - Public `/feedback/:tenantId` still works (unchanged branding); Google remains a thank-you deep link only.

4. **Docs:** Skim `docs/0064-guest-feedback-analytics.md` for API + QR URL format.
