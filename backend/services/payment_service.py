"""Stripe and mock payment service."""

import stripe

from config import settings


def create_checkout_session(assessment_id: str) -> dict:
    """Create a Stripe checkout session or return mock payment URL."""

    if settings.PAYMENT_MODE == "mock":
        return {
            "checkout_url": f"{settings.FRONTEND_URL}/payment/success?assessment_id={assessment_id}&mock=true",
            "mock": True,
            "assessment_id": assessment_id,
        }

    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": settings.REPORT_CURRENCY,
                    "product_data": {
                        "name": "MindIQ Personality Report",
                        "description": "Comprehensive AI-powered Big Five personality assessment report with career recommendations",
                    },
                    "unit_amount": settings.REPORT_PRICE_CENTS,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}&assessment_id={assessment_id}",
        cancel_url=f"{settings.FRONTEND_URL}/results?id={assessment_id}",
        metadata={"assessment_id": assessment_id},
    )

    return {
        "checkout_url": session.url,
        "mock": False,
        "assessment_id": assessment_id,
    }


def verify_payment(session_id: str | None, mock: bool = False) -> bool:
    if mock or settings.PAYMENT_MODE == "mock":
        return True

    if not session_id:
        return False

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.retrieve(session_id)
    return session.payment_status == "paid"
