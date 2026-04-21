import stripe
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.config import STRIPE_SECRET_KEY

stripe.api_key = STRIPE_SECRET_KEY

router = APIRouter(prefix="/checkout", tags=["checkout"])


class OneTimePaymentRequest(BaseModel):
    amount: int = Field(..., gt=0)  # smallest currency unit (cents for USD)
    currency: str = Field("usd", min_length=3, max_length=3)
    product_name: str = "Reference product"
    success_url: str = "http://localhost:8000/success"
    cancel_url: str = "http://localhost:8000/cancel"


class SubscriptionRequest(BaseModel):
    price_id: str
    success_url: str = "http://localhost:8000/success"
    cancel_url: str = "http://localhost:8000/cancel"


@router.post("/payment")
def create_one_time_session(req: OneTimePaymentRequest):
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": req.currency,
                        "product_data": {"name": req.product_name},
                        "unit_amount": req.amount,
                    },
                    "quantity": 1,
                }
            ],
            success_url=req.success_url,
            cancel_url=req.cancel_url,
        )
        return {"id": session.id, "url": session.url}
    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscription")
def create_subscription_session(req: SubscriptionRequest):
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": req.price_id, "quantity": 1}],
            success_url=req.success_url,
            cancel_url=req.cancel_url,
        )
        return {"id": session.id, "url": session.url}
    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
