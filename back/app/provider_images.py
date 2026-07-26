"""Provider product image paths: only expose URLs/refs when the file exists on disk."""

from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, select

from app import models

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"


def provider_product_file_path(provider_token: str, image_filename: str) -> Path:
    """Absolute path for a provider product image file."""
    return UPLOADS_DIR / "providers" / provider_token / "products" / image_filename


def provider_product_image_url(provider_token: str, image_filename: str | None) -> str | None:
    """Public /uploads URL when image_filename is set and the file exists; else None."""
    if not image_filename:
        return None
    fn = image_filename.replace("\\", "/").strip("/")
    if "/" in fn or fn.startswith("."):
        return None
    if not provider_product_file_path(provider_token, fn).is_file():
        return None
    return f"/uploads/providers/{provider_token}/products/{fn}"


def provider_product_stored_image_path(
    provider_token: str, image_filename: str | None
) -> str | None:
    """Relative path stored on Product.image_filename when the file exists; else None."""
    if not image_filename:
        return None
    fn = image_filename.replace("\\", "/").strip("/")
    if "/" in fn or fn.startswith("."):
        return None
    if not provider_product_file_path(provider_token, fn).is_file():
        return None
    return f"providers/{provider_token}/products/{fn}"


def clear_orphan_provider_product_images(session: Session) -> dict[str, int]:
    """
    Clear ProviderProduct.image_filename (and Product refs under providers/) when the file is missing.

    Idempotent. Does not delete rows or files that exist.
    """
    providers = {p.id: p for p in session.exec(select(models.Provider)).all()}
    cleared_pp = 0
    for pp in session.exec(
        select(models.ProviderProduct).where(models.ProviderProduct.image_filename.is_not(None))
    ).all():
        provider = providers.get(pp.provider_id)
        if not provider or not pp.image_filename:
            continue
        fn = pp.image_filename.replace("\\", "/").strip("/")
        if "/" in fn or fn.startswith(".") or not provider_product_file_path(provider.token, fn).is_file():
            pp.image_filename = None
            session.add(pp)
            cleared_pp += 1

    cleared_product = 0
    for product in session.exec(
        select(models.Product).where(models.Product.image_filename.is_not(None))
    ).all():
        fn = (product.image_filename or "").replace("\\", "/").strip("/")
        if not fn.startswith("providers/"):
            continue
        path = UPLOADS_DIR / fn
        if not path.is_file():
            product.image_filename = None
            session.add(product)
            cleared_product += 1

    if cleared_pp or cleared_product:
        session.commit()

    return {
        "provider_products_cleared": cleared_pp,
        "products_cleared": cleared_product,
    }
