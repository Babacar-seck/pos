"""Normalize tenant currency fields for API responses (GitHub #41)."""

# Stripe's documented zero-decimal currencies: the stored integer amount IS the whole unit
# (e.g. 1500 XOF = 1500 francs, not 15.00). See CONTEXT.md: "Devise sans décimales".
ZERO_DECIMAL_CURRENCIES: frozenset[str] = frozenset(
    {
        "BIF", "CLP", "DJF", "GNF", "JPY", "KMF", "KRW", "MGA", "PYG",
        "RWF", "UGX", "VND", "VUV", "XAF", "XOF", "XPF",
    }
)

# Stripe's documented three-decimal currencies (thousandths).
THREE_DECIMAL_CURRENCIES: frozenset[str] = frozenset({"BHD", "JOD", "KWD", "OMR", "TND"})

# Display symbols for common ISO 4217 codes (legacy `Tenant.currency` column + JSON fields).
_DISPLAY_SYMBOL_BY_ISO: dict[str, str] = {
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "JPY": "¥",
    "MXN": "$",
    "CHF": "CHF",
    "CAD": "C$",
    "AUD": "A$",
    "INR": "₹",
    "CNY": "¥",
    "TWD": "NT$",
    "BRL": "R$",
    "PLN": "zł",
    "SEK": "kr",
    "NOK": "kr",
    "DKK": "kr",
    "NZD": "NZ$",
    "KRW": "₩",
    "ILS": "₪",
    "ZAR": "R",
    "HKD": "HK$",
    "SGD": "S$",
    "THB": "฿",
    "MYR": "RM",
    "PHP": "₱",
    "CZK": "Kč",
    "HUF": "Ft",
}


def normalize_tenant_currency_fields(
    currency_code: str | None,
    currency: str | None,
) -> tuple[str, str]:
    """Return (iso_code, display_symbol). Missing code defaults to EUR/€."""
    code = (currency_code or "").strip().upper()
    if not code:
        return ("EUR", "€")
    sym = _DISPLAY_SYMBOL_BY_ISO.get(code)
    if sym is not None:
        return (code, sym)
    legacy = (currency or "").strip()
    return (code, legacy if legacy else code)


def default_decimal_places(currency_code: str | None) -> int:
    """Decimal places conventionally used by an ISO 4217 code (Stripe zero/three-decimal lists)."""
    code = (currency_code or "").strip().upper()
    if code in ZERO_DECIMAL_CURRENCIES:
        return 0
    if code in THREE_DECIMAL_CURRENCIES:
        return 3
    return 2


def resolve_tenant_decimal_places(
    currency_code: str | None,
    currency_decimal_places: int | None,
) -> int:
    """Explicit tenant override wins; otherwise derive from currency_code."""
    if currency_decimal_places is not None:
        return currency_decimal_places
    return default_decimal_places(currency_code)


def to_display_amount(minor_units: int, decimal_places: int) -> float:
    """Stored integer amount -> display number (1234, 2 -> 12.34; 1234, 0 -> 1234)."""
    return minor_units / (10**decimal_places)


def to_minor_units(display_amount: float, decimal_places: int) -> int:
    """Display number -> stored integer amount, rounded to the nearest unit."""
    return round(display_amount * (10**decimal_places))


def apply_tenant_currency_api_dict(d: dict) -> None:
    """Mutate tenant-like dict in place for consistent currency_code + currency + decimal_places."""
    c, s = normalize_tenant_currency_fields(d.get("currency_code"), d.get("currency"))
    d["currency_code"] = c
    d["currency"] = s
    d["currency_decimal_places_resolved"] = resolve_tenant_decimal_places(
        c, d.get("currency_decimal_places")
    )


def sync_tenant_currency_symbol_from_code(currency_code: str | None) -> str | None:
    """Canonical display symbol to store on Tenant.currency when ISO code is set."""
    if not currency_code or not isinstance(currency_code, str):
        return None
    raw = currency_code.strip().upper()
    if len(raw) != 3 or not raw.isalpha():
        return None
    _, sym = normalize_tenant_currency_fields(raw, None)
    return sym
