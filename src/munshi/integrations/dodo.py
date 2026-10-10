"""Dodo Payments (test mode): turn a drafted invoice into a payment link, and check whether it was paid."""

from decimal import Decimal

import httpx

from munshi import tracing
from munshi.config import settings

BASE = "https://test.dodopayments.com"


def _headers() -> dict:
    if not settings.dodo_api_key:
        raise RuntimeError("DODO_API_KEY missing in .env")
    return {"Authorization": f"Bearer {settings.dodo_api_key}", "Content-Type": "application/json"}


@tracing.span("TOOL", name="dodo_payment_link")
def payment_link(invoice_number: str, description: str, total_inr: Decimal, client_name: str,
                 client_email: str) -> dict:
    """Create a one-time product for the invoice (amount in paise, tax inclusive) and a checkout session."""
    product = httpx.post(f"{BASE}/products", headers=_headers(), timeout=30, json={
        "name": f"Invoice {invoice_number}",
        "description": description,
        "price": {"type": "one_time_price", "currency": "INR", "price": int(total_inr * 100),
                  "discount": 0, "purchasing_power_parity": False, "tax_inclusive": True},
        "tax_category": "saas",
    })
    product.raise_for_status()
    product_id = product.json()["product_id"]
    session = httpx.post(f"{BASE}/checkouts", headers=_headers(), timeout=30, json={
        "product_cart": [{"product_id": product_id, "quantity": 1}],
        "customer": {"email": client_email, "name": client_name},
        "metadata": {"invoice_number": invoice_number, "source": "munshi"},
    })
    session.raise_for_status()
    data = session.json()
    return {"product_id": product_id, "session_id": data.get("session_id"),
            "checkout_url": data.get("checkout_url"), "amount": str(total_inr)}


@tracing.span("TOOL", name="dodo_payments_for_invoice")
def payments_for(invoice_number: str) -> list[dict]:
    """Succeeded payments carrying this invoice number in metadata (polling instead of webhooks)."""
    r = httpx.get(f"{BASE}/payments", headers=_headers(), timeout=30, params={"page_size": 100})
    r.raise_for_status()
    return [p for p in r.json().get("items", [])
            if (p.get("metadata") or {}).get("invoice_number") == invoice_number and p.get("status") == "succeeded"]
