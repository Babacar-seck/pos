-- Per-tenant override for number of decimal places used to display/enter money amounts (#345).
-- NULL = derive default from currency_code (Stripe zero/three-decimal currency lists, see app/currency_utils.py).
-- Explicit value (0, 2, 3...) lets the manager override the currency's usual convention.

ALTER TABLE tenant
    ADD COLUMN IF NOT EXISTS currency_decimal_places INTEGER;
