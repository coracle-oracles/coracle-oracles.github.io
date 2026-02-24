import logging
from datetime import timedelta

import stripe
from django.conf import settings
from django.tasks import task
from django.utils import timezone

from .models import Order

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

RECONCILIATION_INTERVAL_MINUTES = 10


@task
def reconcile_pending_orders(max_age_minutes=60):
    """
    Reconcile pending orders by checking their status with Stripe.

    Finds orders that are still pending after a grace period and verifies
    their payment status directly with Stripe's API.

    This task reschedules itself to run every 10 minutes.
    """
    cutoff = timezone.now() - timedelta(minutes=5)
    max_age = timezone.now() - timedelta(minutes=max_age_minutes)

    pending_orders = Order.objects.filter(
        status='pending',
        created_at__lt=cutoff,
        created_at__gt=max_age,
    )

    reconciled = 0
    for order in pending_orders:
        try:
            session = stripe.checkout.Session.retrieve(order.stripe_checkout_session_id)

            if session.payment_status == 'paid':
                order.status = 'completed'
                order.stripe_payment_intent_id = session.payment_intent
                order.save()
                reconciled += 1
                logger.info(f"Reconciled order {order.id} - marked as completed")
            elif session.status == 'expired':
                order.status = 'cancelled'
                order.save()
                logger.info(f"Reconciled order {order.id} - marked as cancelled (session expired)")
        except stripe.error.StripeError as e:
            logger.warning(f"Failed to reconcile order {order.id}: {e}")

    logger.info(f"Reconciliation complete: {reconciled} orders updated")

    # Reschedule this task to run again
    reconcile_pending_orders.enqueue(
        run_after=timezone.now() + timedelta(minutes=RECONCILIATION_INTERVAL_MINUTES)
    )

    return reconciled
