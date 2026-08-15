from app.tenant_currency import (
    apply_tenant_currency_api_dict,
    default_decimal_places,
    normalize_tenant_currency_fields,
    resolve_tenant_decimal_places,
    sync_tenant_currency_symbol_from_code,
    to_display_amount,
    to_minor_units,
)


def test_normalize_defaults_to_eur():
    assert normalize_tenant_currency_fields(None, None) == ("EUR", "€")
    assert normalize_tenant_currency_fields("", "$") == ("EUR", "€")


def test_normalize_usd():
    assert normalize_tenant_currency_fields("usd", None) == ("USD", "$")


def test_apply_dict_mutates():
    d = {"currency_code": None, "currency": "$"}
    apply_tenant_currency_api_dict(d)
    assert d["currency_code"] == "EUR"
    assert d["currency"] == "€"


def test_apply_dict_keeps_usd():
    d = {"currency_code": "USD", "currency": "€"}
    apply_tenant_currency_api_dict(d)
    assert d["currency_code"] == "USD"
    assert d["currency"] == "$"


def test_sync_symbol():
    assert sync_tenant_currency_symbol_from_code("EUR") == "€"
    assert sync_tenant_currency_symbol_from_code(None) is None


def test_default_decimal_places():
    assert default_decimal_places("EUR") == 2
    assert default_decimal_places("XOF") == 0
    assert default_decimal_places("xaf") == 0  # case-insensitive
    assert default_decimal_places("JPY") == 0
    assert default_decimal_places("BHD") == 3
    assert default_decimal_places(None) == 2
    assert default_decimal_places("") == 2


def test_resolve_tenant_decimal_places_override_wins():
    assert resolve_tenant_decimal_places("XOF", None) == 0
    assert resolve_tenant_decimal_places("XOF", 2) == 2  # explicit override
    assert resolve_tenant_decimal_places("EUR", 0) == 0  # explicit override
    assert resolve_tenant_decimal_places("EUR", None) == 2


def test_to_display_amount_and_to_minor_units_roundtrip():
    assert to_display_amount(1500, 2) == 15.0
    assert to_display_amount(1500, 0) == 1500
    assert to_minor_units(15.0, 2) == 1500
    assert to_minor_units(1500, 0) == 1500
    assert to_minor_units(12.34, 2) == 1234
    assert to_minor_units(12.346, 2) == 1235  # rounds to nearest minor unit


def test_apply_dict_includes_resolved_decimal_places():
    d = {"currency_code": "XOF", "currency": None, "currency_decimal_places": None}
    apply_tenant_currency_api_dict(d)
    assert d["currency_decimal_places_resolved"] == 0

    d2 = {"currency_code": "EUR", "currency": None, "currency_decimal_places": 0}
    apply_tenant_currency_api_dict(d2)
    assert d2["currency_decimal_places_resolved"] == 0  # override respected even against EUR default
