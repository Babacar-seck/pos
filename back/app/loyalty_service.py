"""Club loyalty: earn on paid orders, redeem at checkout, append-only ledger (#327)."""

from __future__ import annotations

import calendar
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlmodel import Session, select

from . import models


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _valid_birthday(month: int | None, day: int | None) -> tuple[int, int] | None:
    """Return (month, day) or None if both omitted; raise 400 if invalid/partial."""
    if month is None and day is None:
        return None
    if month is None or day is None:
        raise HTTPException(status_code=400, detail="birthday_month and birthday_day must be set together")
    m, d = int(month), int(day)
    if m < 1 or m > 12 or d < 1 or d > 31:
        raise HTTPException(status_code=400, detail="Invalid birthday month/day")
    # Allow Feb 29; award on Feb 28 in non-leap years.
    max_day = 29 if m == 2 else calendar.monthrange(2024 if m == 2 else 2021, m)[1]
    if d > max_day:
        raise HTTPException(status_code=400, detail="Invalid birthday month/day")
    return m, d


def get_program(session: Session, tenant_id: int) -> models.LoyaltyProgram | None:
    return session.exec(
        select(models.LoyaltyProgram).where(models.LoyaltyProgram.tenant_id == tenant_id)
    ).first()


def get_or_create_program(session: Session, tenant_id: int) -> models.LoyaltyProgram:
    program = get_program(session, tenant_id)
    if program:
        return program
    program = models.LoyaltyProgram(tenant_id=tenant_id)
    session.add(program)
    session.flush()
    return program


def program_to_dict(program: models.LoyaltyProgram) -> dict:
    return {
        "id": program.id,
        "tenant_id": program.tenant_id,
        "enabled": program.enabled,
        "program_name": program.program_name,
        "mode": program.mode,
        "earn_units_per_order": program.earn_units_per_order,
        "redemption_threshold": program.redemption_threshold,
        "reward_discount_cents": program.reward_discount_cents,
        "birthday_bonus_units": int(getattr(program, "birthday_bonus_units", 0) or 0),
        "created_at": program.created_at.isoformat() if program.created_at else None,
        "updated_at": program.updated_at.isoformat() if program.updated_at else None,
    }


def membership_to_dict(
    membership: models.LoyaltyMembership,
    *,
    include_token: bool = False,
) -> dict:
    data = {
        "id": membership.id,
        "tenant_id": membership.tenant_id,
        "program_id": membership.program_id,
        "billing_customer_id": membership.billing_customer_id,
        "display_name": membership.display_name,
        "email": membership.email,
        "phone": membership.phone,
        "balance": membership.balance,
        "birthday_month": getattr(membership, "birthday_month", None),
        "birthday_day": getattr(membership, "birthday_day", None),
        "birthday_bonus_year": getattr(membership, "birthday_bonus_year", None),
        "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
        "updated_at": membership.updated_at.isoformat() if membership.updated_at else None,
    }
    if include_token:
        data["member_token"] = membership.member_token
    return data


def ledger_to_dict(entry: models.LoyaltyLedgerEntry) -> dict:
    return {
        "id": entry.id,
        "tenant_id": entry.tenant_id,
        "membership_id": entry.membership_id,
        "entry_type": entry.entry_type,
        "units": entry.units,
        "balance_after": entry.balance_after,
        "order_id": entry.order_id,
        "note": entry.note,
        "created_by_user_id": entry.created_by_user_id,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


def _new_member_token() -> str:
    return secrets.token_urlsafe(24)


def _apply_ledger(
    session: Session,
    *,
    membership: models.LoyaltyMembership,
    entry_type: str,
    units: int,
    order_id: int | None = None,
    note: str | None = None,
    created_by_user_id: int | None = None,
) -> models.LoyaltyLedgerEntry:
    """Append a ledger row and update cached balance. `units` is signed (earn +, redeem -)."""
    new_balance = membership.balance + units
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Loyalty balance cannot go negative")
    membership.balance = new_balance
    membership.updated_at = _now()
    entry = models.LoyaltyLedgerEntry(
        tenant_id=membership.tenant_id,
        membership_id=membership.id,  # type: ignore[arg-type]
        entry_type=entry_type,
        units=units,
        balance_after=new_balance,
        order_id=order_id,
        note=note,
        created_by_user_id=created_by_user_id,
    )
    session.add(membership)
    session.add(entry)
    session.flush()
    return entry


def join_program(
    session: Session,
    *,
    tenant_id: int,
    display_name: str,
    email: str | None = None,
    phone: str | None = None,
    billing_customer_id: int | None = None,
    birthday_month: int | None = None,
    birthday_day: int | None = None,
) -> models.LoyaltyMembership:
    program = get_program(session, tenant_id)
    if not program or not program.enabled:
        raise HTTPException(status_code=404, detail="Loyalty program is not enabled")
    name = (display_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="display_name is required")
    if not email and not phone:
        raise HTTPException(status_code=400, detail="email or phone is required")
    bday = _valid_birthday(birthday_month, birthday_day)

    if email:
        existing = session.exec(
            select(models.LoyaltyMembership).where(
                models.LoyaltyMembership.tenant_id == tenant_id,
                models.LoyaltyMembership.email == email,
            )
        ).first()
        if existing:
            if bday and (
                getattr(existing, "birthday_month", None) is None
                or getattr(existing, "birthday_day", None) is None
            ):
                existing.birthday_month, existing.birthday_day = bday
                existing.updated_at = _now()
                session.add(existing)
                session.flush()
            return existing
    if phone:
        existing = session.exec(
            select(models.LoyaltyMembership).where(
                models.LoyaltyMembership.tenant_id == tenant_id,
                models.LoyaltyMembership.phone == phone,
            )
        ).first()
        if existing:
            if bday and (
                getattr(existing, "birthday_month", None) is None
                or getattr(existing, "birthday_day", None) is None
            ):
                existing.birthday_month, existing.birthday_day = bday
                existing.updated_at = _now()
                session.add(existing)
                session.flush()
            return existing

    membership = models.LoyaltyMembership(
        tenant_id=tenant_id,
        program_id=program.id,  # type: ignore[arg-type]
        billing_customer_id=billing_customer_id,
        display_name=name[:200],
        email=email,
        phone=phone,
        member_token=_new_member_token(),
        balance=0,
        birthday_month=bday[0] if bday else None,
        birthday_day=bday[1] if bday else None,
    )
    session.add(membership)
    session.flush()
    return membership


def _is_birthday_today(membership: models.LoyaltyMembership, when: datetime) -> bool:
    month = getattr(membership, "birthday_month", None)
    day = getattr(membership, "birthday_day", None)
    if not month or not day:
        return False
    today = when.astimezone(timezone.utc).date()
    if month == 2 and day == 29 and not calendar.isleap(today.year):
        return today.month == 2 and today.day == 28
    return today.month == month and today.day == day


def _birthday_bonus_pending(
    program: models.LoyaltyProgram,
    membership: models.LoyaltyMembership,
    order: models.Order,
) -> tuple[int, int] | None:
    """Return (bonus_units, year) if a birthday bonus should be awarded; else None."""
    bonus = int(getattr(program, "birthday_bonus_units", 0) or 0)
    if bonus <= 0:
        return None
    paid_at = order.paid_at or _now()
    if not _is_birthday_today(membership, paid_at):
        return None
    year = paid_at.astimezone(timezone.utc).year
    if getattr(membership, "birthday_bonus_year", None) == year:
        return None
    return bonus, year


def maybe_award_birthday_bonus_standalone(
    session: Session,
    *,
    program: models.LoyaltyProgram,
    membership: models.LoyaltyMembership,
    order: models.Order,
) -> models.LoyaltyLedgerEntry | None:
    """Award birthday bonus with order_id=NULL (unique earn-per-order index allows only one earn/order)."""
    pending = _birthday_bonus_pending(program, membership, order)
    if not pending:
        return None
    bonus, year = pending
    note = f"Birthday bonus {year}"
    existing = session.exec(
        select(models.LoyaltyLedgerEntry).where(
            models.LoyaltyLedgerEntry.membership_id == membership.id,
            models.LoyaltyLedgerEntry.entry_type == "earn",
            models.LoyaltyLedgerEntry.note == note,
        )
    ).first()
    if existing:
        membership.birthday_bonus_year = year
        session.add(membership)
        return existing
    entry = _apply_ledger(
        session,
        membership=membership,
        entry_type="earn",
        units=bonus,
        order_id=None,
        note=note,
    )
    membership.birthday_bonus_year = year
    session.add(membership)
    session.flush()
    return entry


def award_on_order_paid(session: Session, order: models.Order) -> models.LoyaltyLedgerEntry | None:
    """Award earn units once per paid order when a membership is linked. Safe to call repeatedly.

    Birthday bonus (once per year) is folded into the same earn row when possible so the
    unique (order_id, earn) index is respected; otherwise awarded as a standalone earn
    with order_id NULL (#327 / #331).
    """
    if not order or not order.id or not order.paid_at:
        return None
    if not order.loyalty_membership_id:
        return None

    program = get_program(session, order.tenant_id)
    if not program or not program.enabled:
        return None

    membership = session.get(models.LoyaltyMembership, order.loyalty_membership_id)
    if not membership or membership.tenant_id != order.tenant_id:
        return None

    # Sync birthday from linked billing customer when membership has none.
    if (
        membership.billing_customer_id
        and getattr(membership, "birthday_month", None) is None
        and getattr(membership, "birthday_day", None) is None
    ):
        bc = session.get(models.BillingCustomer, membership.billing_customer_id)
        if bc and bc.birth_date:
            membership.birthday_month = bc.birth_date.month
            membership.birthday_day = bc.birth_date.day
            session.add(membership)

    existing = session.exec(
        select(models.LoyaltyLedgerEntry).where(
            models.LoyaltyLedgerEntry.order_id == order.id,
            models.LoyaltyLedgerEntry.entry_type == "earn",
        )
    ).first()
    if existing:
        # Earn already recorded for this order; still try standalone birthday if pending.
        maybe_award_birthday_bonus_standalone(
            session, program=program, membership=membership, order=order
        )
        return existing

    units = int(program.earn_units_per_order or 0)
    note = "Auto-earn on paid order"
    pending = _birthday_bonus_pending(program, membership, order)
    if pending:
        bonus, year = pending
        units += bonus
        note = f"Auto-earn on paid order (+ birthday bonus {year})"
        membership.birthday_bonus_year = year
        session.add(membership)

    if units <= 0:
        if pending:
            return maybe_award_birthday_bonus_standalone(
                session, program=program, membership=membership, order=order
            )
        return None

    return _apply_ledger(
        session,
        membership=membership,
        entry_type="earn",
        units=units,
        order_id=order.id,
        note=note,
    )


def redeem_on_order(
    session: Session,
    *,
    order: models.Order,
    membership: models.LoyaltyMembership,
    created_by_user_id: int | None = None,
) -> dict:
    """Redeem one reward on an unpaid order. Sets loyalty_discount_cents (order-level via #322 helper)."""
    if order.tenant_id != membership.tenant_id:
        raise HTTPException(status_code=404, detail="Membership not found")
    if order.paid_at or order.status == models.OrderStatus.paid:
        raise HTTPException(status_code=400, detail="Cannot redeem on a paid order")
    if order.loyalty_units_redeemed and order.loyalty_units_redeemed > 0:
        raise HTTPException(status_code=400, detail="Loyalty reward already applied to this order")

    program = get_program(session, order.tenant_id)
    if not program or not program.enabled:
        raise HTTPException(status_code=404, detail="Loyalty program is not enabled")
    if membership.balance < program.redemption_threshold:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance (need {program.redemption_threshold})",
        )

    units = -program.redemption_threshold
    _apply_ledger(
        session,
        membership=membership,
        entry_type="redeem",
        units=units,
        order_id=order.id,
        note="Redeem reward at checkout",
        created_by_user_id=created_by_user_id,
    )
    order.loyalty_membership_id = membership.id
    order.loyalty_discount_cents = program.reward_discount_cents
    order.loyalty_units_redeemed = program.redemption_threshold
    session.add(order)
    session.flush()
    return {
        "order_id": order.id,
        "membership_id": membership.id,
        "units_redeemed": program.redemption_threshold,
        "discount_cents": program.reward_discount_cents,
        "balance": membership.balance,
    }


def adjust_balance(
    session: Session,
    *,
    membership: models.LoyaltyMembership,
    delta_units: int,
    note: str | None,
    created_by_user_id: int,
) -> models.LoyaltyLedgerEntry:
    if delta_units == 0:
        raise HTTPException(status_code=400, detail="delta_units must be non-zero")
    return _apply_ledger(
        session,
        membership=membership,
        entry_type="adjust",
        units=delta_units,
        note=(note or "Manual adjustment")[:500],
        created_by_user_id=created_by_user_id,
    )


def wallet_pass_status() -> dict:
    """Operational status for Apple/Google Wallet (certs required; see docs/0066)."""
    from .settings import settings

    apple_ready = bool(
        getattr(settings, "loyalty_apple_pass_cert_path", "")
        and getattr(settings, "loyalty_apple_pass_key_path", "")
        and getattr(settings, "loyalty_apple_wwdr_cert_path", "")
        and getattr(settings, "loyalty_apple_pass_type_id", "")
        and getattr(settings, "loyalty_apple_team_id", "")
    )
    google_ready = bool(
        getattr(settings, "loyalty_google_issuer_id", "")
        and getattr(settings, "loyalty_google_service_account_json", "")
    )
    return {
        "apple_wallet_configured": apple_ready,
        "google_wallet_configured": google_ready,
        "apple_wallet_available": False,  # signing not shipped until certs + PassKit packager
        "google_wallet_available": False,
        "detail": (
            "Wallet pass issuance requires Apple PassKit signing certificates and/or a Google Wallet "
            "issuer + service account. See docs/0066-club-loyalty.md. Do not invent signing formats."
        ),
    }
