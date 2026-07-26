# Split bill / partial payments (#318)

## MVP decision: split **by amount**

Staff records one or more **payment legs** against a single `Order`. Each leg has an amount (cents), a payment method, and an optional payer label. The order stays unpaid until the sum of non-voided legs covers the order due (line items − order-level discounts + tip when tip is applied on settlement).

| Option | MVP | Notes |
|--------|-----|--------|
| **By amount** | **Chosen** | Fast path for “two cards / cash + card”; clear audit rows. |
| By line | Deferred | Needs line allocation UI and partial Factura line rules. |
| By guest session | Deferred | Useful with multi-session tables; align later with table groups. |

## Data model

- **`order_payment`** (tenant-scoped): `order_id`, `amount_cents`, `payment_method`, optional `payer_label`, `paid_by_user_id`, `paid_at`, optional `tip_amount_cents` (usually on the settling leg), optional `stripe_payment_intent_id` (reserved), `voided_at` (soft cancel).
- **`Order.paid_at` / `payment_method` / `status=paid`**: set only when the order is **fully settled**. If multiple methods were used, `payment_method` is stored as `split`.
- Reconciliation (API): `amount_due_cents`, `amount_paid_cents`, `amount_remaining_cents`, `payments[]`.

## Staff API

| Method | Path | Behaviour |
|--------|------|-----------|
| **GET** | `/orders/{id}/payments` | List non-voided (and optionally voided) legs + totals. |
| **POST** | `/orders/{id}/payments` | Record a partial or settling payment. Rejects overpay beyond due + small tolerance. When remaining hits 0 → marks order paid and awards loyalty **once**. |
| **DELETE** | `/orders/{id}/payments/{payment_id}` | Void a leg (only while order is not fiscally locked / not fully paid, or via unmark flow). |
| **PUT** | `/orders/{id}/mark-paid` | Pays **remaining** balance in one leg (creates `order_payment`), then marks paid. Same permission as today. |
| **PUT** | `/orders/{id}/unmark-paid` | Clears paid mark and **voids all** payment legs for that order. |

Permission: existing **`order:mark_paid`**.

## Stripe

- **MVP:** staff-recorded **cash / terminal / other** (and existing single-intent guest Stripe confirm still settles the whole order as one leg).
- **Deferred:** multiple PaymentIntents or partial capture per leg. Prefer **multiple intents** later (cleaner audit than partial capture on one intent). Guest Stripe confirm writes one `order_payment` row with `stripe_payment_intent_id` when settling.

## Factura / VeriFactu

- **MVP:** **one fiscal alta per order** after the order is fully paid (existing `FiscalInvoice` idempotency on `order_id`). Split notation is operational (payment legs), not separate tax invoices per payer.
- **Deferred:** one Factura per payer (would need sequential numbers per payment and legal review). See `docs/0018-verifactu-fiscal-invoicing.md`.

## Loyalty (#327) and promos (#322)

- Loyalty **earn** runs only when the order becomes fully paid (`award_on_order_paid`), not on each partial leg.
- Order-level discounts (loyalty redeem / promos) reduce **amount due** before payment allocation; they are not re-applied per leg.

## Table groups

Merged parties (join tables) still share one order or the existing group UX; split-by-amount works on that order without requiring unjoin. Line/session splits remain future work.

## UI

On **Orders** → Mark as paid / Finish modal: show amount due, payments already recorded, remaining, and **Record partial payment** (amount + method + optional payer label). Full **Mark as paid** settles the remainder.
