# Club loyalty (points / stamps)

**Status:** MVP + VIP tiers + referral (#327 / #334). Wallet pass **issuance** (Apple PassKit `.pkpass` / Google Wallet API) is **gated on operational certificates** and is not signed in-app until those are configured — see below.

## Goal

Tenant-scoped loyalty distinct from pricing promos (**#322**):

- Guests join via public URL `/loyalty/{tenantId}` (optional `?ref=` referral code)
- Staff enable rules under **Settings → Loyalty club**
- Units (points or stamps) earn **once per paid order** when the order is linked to a membership
- Staff redeem a reward at checkout → `order.loyalty_discount_cents` (order-level discount via `order_discounts.order_level_discount_cents`, shared with #322)
- Balance never goes negative (ledger + check)
- **VIP tiers** from lifetime earn; **referral** awards on successful referred join

## Data model

| Table | Role |
|-------|------|
| `loyalty_program` | One row per tenant: enabled, mode (`points`\|`stamps`), earn rate, redemption threshold, reward discount cents, optional `birthday_bonus_units`, VIP thresholds (`vip_silver_min_lifetime_units`, `vip_gold_min_lifetime_units`), referral bonuses |
| `loyalty_membership` | Member identity (name + email/phone), opaque `member_token`, cached `balance`, `lifetime_earn_units`, opaque `referral_code`, optional `referred_by_membership_id`, birthday fields |
| `loyalty_ledger_entry` | Append-only `earn` / `redeem` / `adjust`; optional `order_id`; unique earn-per-order; unique referral-reward note per invitee |
| `order` columns | `loyalty_membership_id`, `loyalty_discount_cents`, `loyalty_units_redeemed` |

Migrations: `back/migrations/20260726162500_club_loyalty.sql`, `20260726223000_split_by_line_and_loyalty_birthday.sql`, `20260727073523_loyalty_vip_referral.sql`.

## VIP tiers (#334)

**Rule:** Tier is derived from **lifetime earn** (`lifetime_earn_units` = sum of positive `earn` ledger units), **not** current balance. Redeeming or adjusting does **not** demote VIP.

| Threshold (program) | Effect |
|---------------------|--------|
| `vip_silver_min_lifetime_units` | ≥ value → `silver` (0 = silver off) |
| `vip_gold_min_lifetime_units` | ≥ value → `gold` (0 = gold off; must be ≥ silver when both > 0) |

Membership API payloads include `vip_tier` (`null` \| `"silver"` \| `"gold"`). Shown on staff member list and public balance card.

## Referral rewards (#334)

**Award trigger:** once when a **new** membership is created with a valid `referral_code` (not on returning join by same email/phone).

- Each member gets an opaque `referral_code`; share link `/loyalty/{tenantId}?ref={code}`.
- Program: `referral_bonus_units` → referrer; optional `referral_invitee_bonus_units` → invitee (0 = that side off).
- Ledger: referrer `earn` with note `Referral reward for membership {invitee_id}` (unique index prevents double-claim); invitee flag `referral_reward_granted`.
- **Self-referral** rejected (same email/phone as referrer, or same membership id).
- Invalid code → 400. Returning existing member → no second referral award.

## Earn / redeem

- **Earn:** after `paid_at` is set (`mark-paid`, `finish`, Stripe/Revolut confirm), `loyalty_service.award_on_order_paid` runs if `loyalty_membership_id` is set. Idempotent (one `earn` ledger row per order). Also increments `lifetime_earn_units`.
- **Birthday bonus (#331):** when `birthday_bonus_units > 0` and the member’s month/day matches `paid_at` (UTC), extra units are folded into that earn row (or a standalone earn with `order_id` null if the order already had an earn). Once per calendar year (`birthday_bonus_year`). Join accepts optional birthday; linked `BillingCustomer.birth_date` can seed month/day.
- **Redeem:** `POST /orders/{id}/loyalty/redeem` with `membership_id` or `member_token`. Requires balance ≥ threshold; writes `redeem` ledger row and sets order discount fields.
- **Manual adjust:** `POST /loyalty/memberships/{id}/adjust` — **owner/admin** (`loyalty:write`) only. Adjust does **not** change lifetime earn / VIP.
- **Permissions:** `loyalty:read`, `loyalty:write` (program + adjust), `loyalty:redeem` (waiter+).
- **Still deferred:** Wallet pass signing until certs are configured.

## APIs (summary)

- Public: `GET/POST /public/tenants/{id}/loyalty`, `GET /public/loyalty/members/{token}`, wallet status endpoint
- Staff: `GET/PUT /loyalty/program`, memberships list/detail/adjust, order link + redeem

Public loyalty GETs use `@public_menu_ip_limit()` (not `@limiter.limit(public_menu_ip_limit)` — that passes the helper function instead of a rate string and 500s under live SlowAPI). Join uses a dedicated per-hour limit. All SlowAPI-wrapped handlers take `request: Request` and `response: Response` so rate-limit headers inject correctly.

## Interaction with #322 (price promos)

Line-level category % promos reduce `OrderItem.price_cents` and store a promo audit snapshot (`docs/0068-price-promotions.md`). Loyalty redemption remains an **order-level** discount on `loyalty_discount_cents`, subtracted through `order_discounts.order_level_discount_cents` for guest checkout, staff totals, and fiscal amount. Do not invent a parallel order-level discount column.

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

See pytest `back/tests/test_club_loyalty.py` (tenant isolation, earn-once, redeem, non-negative balance, wallet unconfigured, VIP tier, referral award-once).
