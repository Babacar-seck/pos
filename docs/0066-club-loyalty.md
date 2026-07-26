# Club loyalty (points / stamps)

**Status:** MVP shipped (#327). Wallet pass **issuance** (Apple PassKit `.pkpass` / Google Wallet API) is **gated on operational certificates** and is not signed in-app until those are configured — see below.

## Goal

Tenant-scoped loyalty distinct from pricing promos (**#322**):

- Guests join via public URL `/loyalty/{tenantId}`
- Staff enable rules under **Settings → Loyalty club**
- Units (points or stamps) earn **once per paid order** when the order is linked to a membership
- Staff redeem a reward at checkout → `order.loyalty_discount_cents` (temporary discount field until #322’s promo/audit path exists)
- Balance never goes negative (ledger + check)

## Data model

| Table | Role |
|-------|------|
| `loyalty_program` | One row per tenant: enabled, mode (`points`\|`stamps`), earn rate, redemption threshold, reward discount cents |
| `loyalty_membership` | Member identity (name + email/phone), opaque `member_token`, cached `balance` |
| `loyalty_ledger_entry` | Append-only `earn` / `redeem` / `adjust`; optional `order_id`; unique earn-per-order |
| `order` columns | `loyalty_membership_id`, `loyalty_discount_cents`, `loyalty_units_redeemed` |

Migration: `back/migrations/20260726162500_club_loyalty.sql`.

## Earn / redeem

- **Earn:** after `paid_at` is set (`mark-paid`, `finish`, Stripe/Revolut confirm), `loyalty_service.award_on_order_paid` runs if `loyalty_membership_id` is set. Idempotent (one `earn` ledger row per order).
- **Redeem:** `POST /orders/{id}/loyalty/redeem` with `membership_id` or `member_token`. Requires balance ≥ threshold; writes `redeem` ledger row and sets order discount fields.
- **Manual adjust:** `POST /loyalty/memberships/{id}/adjust` — **owner/admin** (`loyalty:write`) only.
- **Permissions:** `loyalty:read`, `loyalty:write` (program + adjust), `loyalty:redeem` (waiter+).

## APIs (summary)

- Public: `GET/POST /public/tenants/{id}/loyalty`, `GET /public/loyalty/members/{token}`, wallet status endpoint
- Staff: `GET/PUT /loyalty/program`, memberships list/detail/adjust, order link + redeem

## Interaction with #322 (price promos)

#322 is **not** implemented yet. Loyalty redemption uses `order.loyalty_discount_cents` and subtracts it from payable totals. When #322 lands, fold this into the same discount/audit mechanism (do not invent a second parallel system). Factura / tax lines should treat the loyalty discount like other order-level discounts once that path exists.

## Wallet: Apple PassKit & Google Wallet

**Do not invent signing formats.** Follow official docs:

- Apple: [Wallet Developer Guide / PassKit](https://developer.apple.com/documentation/walletpasses) — `.pkpass` ZIP with `pass.json`, manifest SHA-1 hashes, PKCS#7 signature using Apple WWDR + Pass Type ID certificate.
- Google: [Google Wallet API](https://developers.google.com/wallet) — issuer account + service account JWT; loyalty object/class updates for balance pushes.

### Operational dependencies (env)

Documented in `config.env.example`:

| Variable | Purpose |
|----------|---------|
| `LOYALTY_APPLE_PASS_TYPE_ID` | Pass Type ID |
| `LOYALTY_APPLE_TEAM_ID` | Apple Team ID |
| `LOYALTY_APPLE_PASS_CERT_PATH` | Pass signing cert (PEM/P12 path on server) |
| `LOYALTY_APPLE_PASS_KEY_PATH` | Private key path |
| `LOYALTY_APPLE_WWDR_CERT_PATH` | Apple WWDR intermediate |
| `LOYALTY_GOOGLE_ISSUER_ID` | Google Wallet issuer |
| `LOYALTY_GOOGLE_SERVICE_ACCOUNT_JSON` | Path to service-account JSON (**never commit**) |

Until these are set and a PassKit/Google packager is wired, `wallet_pass_status()` reports `*_available: false` with a clear detail string. Join still works; balance card is `/loyalty/card/{memberToken}`.

Push-update of an existing pass requires Apple’s web service endpoints / Google object PATCH — deferred until certs are live.

## Testing

See pytest `back/tests/test_club_loyalty.py` (tenant isolation, earn-once, redeem, non-negative balance, wallet unconfigured).
