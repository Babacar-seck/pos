# Birthday guest capture

## GitHub Issues
- **Issue:** https://github.com/satisfecho/pos/issues/324
- **324**

## Problem / goal

Capture **birthdays** for guests generally (not only billing customers), with optional future reminders/campaigns. Billing-customer `birth_date` already exists (Factura CRM / `docs/0017-billing-customers-factura.md`), but reservation and walk-in guests have no birthday field and no automation. From umbrella **#52** (see `docs/0050-github-issue-52-split-plan.md` Phase A). Keep MVP about **data capture + staff visibility**; defer outbound email/SMS until consent/provider exists. Distinct from loyalty birthday rewards (`docs/0066-club-loyalty.md` / **#327**).

## High-level instructions for coder

- Add optional birthday storage for at least one guest path (reservation create/edit and/or public book), preferring month/day-only if full year raises privacy concerns; reuse patterns from billing-customer `birth_date` where sensible.
- Surface the value in staff UI; do **not** send automated outbound messages in this MVP.
- Settings: enable/disable marketing use of birthday data and GDPR consent copy if collecting for campaigns; default to capture-only when unset.
- Do not invent a campaign/discount engine here — birthday promos belong with **#322** (price promos) or loyalty (**#327**), not this issue.
- Tenant-scoped; pytest for create/read and isolation; `CHANGELOG.md` entry; append **Testing instructions**.

## Implementation notes (coder)

- Migration `20260726170000_guest_birthday.sql`: `reservation.guest_birthday_{month,day,marketing_consent}`; tenant `guest_birthday_{capture_enabled,marketing_enabled,consent_text}`.
- Month/day only (no year). Public `/book` shows fields when capture enabled; marketing consent checkbox only when marketing enabled.
- Staff reservations list/create/edit show and edit birthday. Settings under Reservations subsection.
- Docs: `docs/0067-guest-birthday.md`. Pytest: `back/tests/test_guest_birthday.py`.

## Testing instructions

1. **Migrate:** From repo root with stack up:  
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python -m app.migrate`  
   Expect schema version ≥ `20260726170000` and columns present on `reservation` / `tenant`.

2. **Pytest:**  
   `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec back python3 -m pytest tests/test_guest_birthday.py -q`  
   Expect **8 passed** (public settings defaults, staff settings update, staff create/list, public create + consent gating, capture-disabled ignore, invalid day, tenant isolation, clear on update).

3. **Public book UI:** Open `http://127.0.0.1:4202/book/1` (or demo tenant). Confirm optional Birthday month/day selectors. Submit a booking with e.g. March 15; then as staff open Reservations and confirm the card shows the birthday.

4. **Staff create/edit:** On Reservations, create or edit a booked reservation; set month/day; save; confirm list shows birthday. Clear both selects and save; birthday should disappear.

5. **Settings:** Settings → Reservations → Guest birthdays. Toggle **Allow marketing use** on, set consent text, save. Reload `/book/{tenantId}` and confirm consent checkbox appears with that text. Turn marketing off; consent checkbox should hide. Toggle capture off; birthday fields should hide on public book (staff can still set birthday).

6. **Front build:** `docker logs --since 5m pos-front` should show successful bundle generation (no TS errors related to birthday).

7. **Smoke:** `BASE_URL=http://127.0.0.1:4202 npm run test:landing-version --prefix front` should pass.

**Pass:** Steps 1–2 green; birthday visible to staff after public or staff entry; marketing default off / consent only when enabled; no outbound birthday emails/SMS.

**Fail:** Migration missing, pytest failures, birthday not persisted/shown, marketing consent accepted while marketing disabled, or Angular build errors.
