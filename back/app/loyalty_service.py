"""Club loyalty: earn on paid orders, redeem at checkout, append-only ledger (#327)."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlmodel import Session, select

from . import models


def _now() -> datetime:
    return datetime.now(timezone.utc)


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
) -> models.LoyaltyMembership:
    program = get_program(session, tenant_id)
    if not program or not program.enabled:
        raise HTTPException(status_code=404, detail="Loyalty program is not enabled")
    name = (display_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="display_name is required")
    if not email and not phone:
        raise HTTPException(status_code=400, detail="email or phone is required")

    if email:
        existing = session.exec(
            select(models.LoyaltyMembership).where(
                models.LoyaltyMembership.tenant_id == tenant_id,
                models.LoyaltyMembership.email == email,
            )
        ).first()
        if existing:
            return existing
    if phone:
        existing = session.exec(
            select(models.LoyaltyMembership).where(
                models.LoyaltyMembership.tenant_id == tenant_id,
                models.LoyaltyMembership.phone == phone,
            )
        ).first()
        if existing:
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
    )
    session.add(membership)
    session.flush()
    return membership


def award_on_order_paid(session: Session, order: models.Order) -> models.LoyaltyLedgerEntry | None:
    """Award earn units once per paid order when a membership is linked. Safe to call repeatedly."""
    if not order or not order.id or not order.paid_at:
        return None
    if not order.loyalty_membership_id:
        return None

    existing = session.exec(
        select(models.LoyaltyLedgerEntry).where(
            models.LoyaltyLedgerEntry.order_id == order.id,
            models.LoyaltyLedgerEntry.entry_type == "earn",
        )
    ).first()
    if existing:
        return existing

    program = get_program(session, order.tenant_id)
    if not program or not program.enabled or program.earn_units_per_order <= 0:
        return None

    membership = session.get(models.LoyaltyMembership, order.loyalty_membership_id)
    if not membership or membership.tenant_id != order.tenant_id:
        return None

    return _apply_ledger(
        session,
        membership=membership,
        entry_type="earn",
        units=program.earn_units_per_order,
        order_id=order.id,
        note="Auto-earn on paid order",
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
