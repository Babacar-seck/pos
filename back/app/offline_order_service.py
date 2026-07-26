"""Staff offline cash sale → online sync with idempotency (#319)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlmodel import Session, select

from app import models
from app.delivery_order_service import _add_order_items, _resolve_product_lines

TAKE_AWAY_TABLE_NAMES = ("take away", "home ordering", "takeaway", "take-away")


def _is_take_away_table(table: models.Table | None) -> bool:
    if not table or not getattr(table, "name", None):
        return False
    return (table.name or "").strip().lower() in TAKE_AWAY_TABLE_NAMES


def create_offline_cash_order(
    session: Session,
    *,
    tenant_id: int,
    user_id: int,
    idempotency_key: str,
    table_id: int,
    lines: list[dict],
    notes: str | None = None,
    customer_name: str | None = None,
) -> tuple[models.Order | None, dict]:
    """
    Create a paid cash order for an offline-queued staff sale.

    Idempotent on (tenant_id, idempotency_key): replay returns the existing order.
    lines: [{"product_id": int, "quantity": int, "notes": str|None}].
    """
    key = (idempotency_key or "").strip()
    if not key or len(key) > 64:
        return None, {"status": "error", "detail": "invalid_idempotency_key"}

    existing = session.exec(
        select(models.OfflineOrderIdempotency).where(
            models.OfflineOrderIdempotency.tenant_id == tenant_id,
            models.OfflineOrderIdempotency.idempotency_key == key,
        )
    ).first()
    if existing:
        order = session.get(models.Order, existing.order_id)
        if order and order.tenant_id == tenant_id and order.deleted_at is None:
            return order, {"status": "duplicate", "order_id": order.id}
        return None, {"status": "error", "detail": "idempotency_orphan"}

    table = session.get(models.Table, table_id)
    if not table or table.tenant_id != tenant_id:
        return None, {"status": "error", "detail": "table_not_found"}

    # Prefer take-away; allow any tenant table that is active (staff may cash-out a walk-in).
    if not _is_take_away_table(table) and not table.is_active:
        return None, {"status": "error", "detail": "table_not_active"}

    resolved_lines, err = _resolve_product_lines(session, tenant_id=tenant_id, lines=lines)
    if err:
        return None, err
    assert resolved_lines is not None

    now = datetime.now(timezone.utc)
    order = models.Order(
        table_id=table.id,
        tenant_id=tenant_id,
        status=models.OrderStatus.paid,
        session_id=None,
        customer_name=(customer_name or "").strip() or None,
        notes=(notes or "").strip() or None,
        paid_at=now,
        paid_by_user_id=user_id,
        payment_method="cash",
        created_at=now,
    )
    session.add(order)
    session.flush()

    order_date = order.created_at.date() if order.created_at else date.today()
    _add_order_items(
        session,
        order=order,
        tenant_id=tenant_id,
        resolved_lines=resolved_lines,
        order_date=order_date,
    )
    session.flush()

    items = session.exec(
        select(models.OrderItem).where(models.OrderItem.order_id == order.id)
    ).all()
    for item in items:
        if item.status != models.OrderItemStatus.cancelled:
            item.status = models.OrderItemStatus.delivered
            item.status_updated_at = now
            item.delivered_by_user_id = user_id
            session.add(item)

    # Do not leave a paid order as the table's active open ticket.
    if table.active_order_id is None or table.active_order_id == order.id:
        table.active_order_id = None
        session.add(table)

    ledger = models.OfflineOrderIdempotency(
        tenant_id=tenant_id,
        idempotency_key=key,
        order_id=order.id,
        created_at=now,
    )
    session.add(ledger)
    session.add(order)
    # Audit leg so offline cash matches online mark-paid / split-bill ledger (#318).
    try:
        from app.order_payment_service import ensure_full_payment_leg

        ensure_full_payment_leg(
            session,
            order=order,
            payment_method="cash",
            paid_by_user_id=user_id,
            tip_amount_cents=None,
        )
    except Exception:
        pass
    session.commit()
    session.refresh(order)

    try:
        from app.main import publish_order_update

        publish_order_update(
            tenant_id,
            {
                "type": "order_paid",
                "order_id": order.id,
                "table_name": table.name if table else "Unknown",
                "payment_method": "cash",
                "offline_sync": True,
            },
            table_id=order.table_id,
        )
    except Exception:
        pass

    # German TSE: auto-sign sale on offline-cash sync when tenant TSE is enabled (#316 / #331).
    try:
        from app.tse_service import maybe_sign_sale_after_paid

        maybe_sign_sale_after_paid(session, order)
        session.refresh(order)
    except Exception:
        pass

    try:
        tenant = session.get(models.Tenant, tenant_id)
        if tenant and getattr(tenant, "inventory_tracking_enabled", False):
            from app.inventory_service import deduct_inventory_for_order

            deduct_inventory_for_order(session, order, tenant)
            session.commit()
    except Exception:
        pass

    return order, {"status": "created", "order_id": order.id}
