import hmac
import hashlib
import json
import os
import time

import pytest
from fastapi.testclient import TestClient

from src.config import STRIPE_WEBHOOK_SECRET
from src.db import get_connection, init_db
from src.main import app


def _reset_db() -> None:
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM processed_events")
        conn.commit()


def _sign(payload: bytes, secret: str, timestamp: int) -> str:
    signed_payload = f"{timestamp}.{payload.decode()}".encode()
    sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


def _make_event(event_id: str = "evt_test_001") -> bytes:
    event = {
        "id": event_id,
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "customer": "cus_test_456",
                "amount_total": 2000,
                "currency": "usd",
            }
        },
    }
    return json.dumps(event).encode()


@pytest.fixture
def client():
    _reset_db()
    return TestClient(app)


def test_valid_webhook_is_accepted_and_recorded(client):
    payload = _make_event("evt_happy_path_001")
    ts = int(time.time())
    sig = _sign(payload, STRIPE_WEBHOOK_SECRET, ts)

    resp = client.post(
        "/webhook",
        content=payload,
        headers={"stripe-signature": sig, "content-type": "application/json"},
    )

    assert resp.status_code == 200
    assert resp.json() == {"received": True}

    with get_connection() as conn:
        row = conn.execute(
            "SELECT event_id, event_type FROM processed_events WHERE event_id = ?",
            ("evt_happy_path_001",),
        ).fetchone()
    assert row == ("evt_happy_path_001", "checkout.session.completed")


def test_duplicate_event_is_skipped(client):
    payload = _make_event("evt_duplicate_001")
    ts = int(time.time())
    sig = _sign(payload, STRIPE_WEBHOOK_SECRET, ts)
    headers = {"stripe-signature": sig, "content-type": "application/json"}

    first = client.post("/webhook", content=payload, headers=headers)
    second = client.post("/webhook", content=payload, headers=headers)

    assert first.status_code == 200
    assert first.json() == {"received": True}
    assert second.status_code == 200
    assert second.json() == {"received": True, "duplicate": True}


def test_invalid_signature_is_rejected(client):
    payload = _make_event("evt_bad_sig_001")
    ts = int(time.time())
    bad_sig = _sign(payload, "whsec_WRONG_SECRET", ts)

    resp = client.post(
        "/webhook",
        content=payload,
        headers={"stripe-signature": bad_sig, "content-type": "application/json"},
    )

    assert resp.status_code == 400
