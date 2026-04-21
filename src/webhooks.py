import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

import stripe
from fastapi import APIRouter, HTTPException, Request

from src.config import STRIPE_WEBHOOK_SECRET
from src.idempotency import already_processed, mark_processed

router = APIRouter(tags=["webhooks"])

logger = logging.getLogger("stripe.webhooks")
if not logger.handlers:
    _h = logging.StreamHandler(sys.stdout)
    _h.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def _log(event_id: str, event_type: str, status: str, **extra: Any) -> None:
    logger.info(
        json.dumps(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "event_id": event_id,
                "event_type": event_type,
                "status": status,
                **extra,
            }
        )
    )


HANDLED_EVENTS = {
    "checkout.session.completed",
    "invoice.paid",
    "invoice.payment_failed",
    "customer.subscription.deleted",
}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    if not STRIPE_WEBHOOK_SECRET or STRIPE_WEBHOOK_SECRET.startswith("whsec_...") or STRIPE_WEBHOOK_SECRET == "whsec_":
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET is not configured")

    # Raw bytes — HMAC is over the wire payload, re-serialized JSON breaks it.
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        _log("unknown", "unknown", "rejected_invalid_payload")
        raise HTTPException(status_code=400, detail="invalid payload")
    except stripe.SignatureVerificationError:
        _log("unknown", "unknown", "rejected_invalid_signature")
        raise HTTPException(status_code=400, detail="invalid signature")

    event_id = event["id"]
    event_type = event["type"]

    if already_processed(event_id):
        _log(event_id, event_type, "skipped_duplicate")
        return {"received": True, "duplicate": True}

    if event_type in HANDLED_EVENTS:
        _dispatch(event)
        _log(event_id, event_type, "handled")
    else:
        _log(event_id, event_type, "ignored_unhandled_type")

    mark_processed(event_id, event_type)
    return {"received": True}


def _dispatch(event: dict) -> None:
    # Business logic hooks go here per event type. Kept empty on purpose —
    # this is a reference, not an app.
    return
