import json

import stripe
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import CustomUserCreationForm
from .models import Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    return render(request, 'core/index.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})


def survival_guide(request):
    return render(request, 'core/survival_guide.html')


def principles(request):
    return render(request, 'core/principles.html')


def ticket_info(request):
    return render(request, 'core/ticket_info.html')


@login_required
def tickets(request):
    """Display ticket selection page."""
    products = settings.TICKET_PRODUCTS
    return render(request, 'core/tickets.html', {
        'products': products,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@login_required
@require_POST
def create_checkout_session(request):
    """Create a Stripe Checkout session and redirect to it."""
    try:
        line_items = []
        order_items_data = []

        for product_id, product in settings.TICKET_PRODUCTS.items():
            quantity = int(request.POST.get(f'quantity_{product_id}', 0))
            if quantity > 0:
                line_items.append({
                    'price': product['stripe_price_id'],
                    'quantity': quantity,
                })
                order_items_data.append({
                    'product_id': product_id,
                    'product_name': product['name'],
                    'quantity': quantity,
                    'unit_price': product['price'],
                })

        if not line_items:
            messages.error(request, 'Please select at least one ticket.')
            return redirect('tickets')

        # Calculate total
        total_amount = sum(item['quantity'] * item['unit_price'] for item in order_items_data)

        # Create Stripe Checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/checkout/success/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/checkout/cancel/'),
            customer_email=request.user.email,
            metadata={
                'user_id': request.user.id,
                'order_items': json.dumps(order_items_data),
            },
        )

        # Create pending order
        order = Order.objects.create(
            user=request.user,
            stripe_checkout_session_id=checkout_session.id,
            status='pending',
            total_amount=total_amount,
        )

        # Create order items
        for item_data in order_items_data:
            OrderItem.objects.create(
                order=order,
                product_id=item_data['product_id'],
                product_name=item_data['product_name'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
            )

        return redirect(checkout_session.url)

    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('tickets')


@login_required
def checkout_success(request):
    """Handle successful checkout."""
    session_id = request.GET.get('session_id')
    if session_id:
        try:
            # Update order status
            order = Order.objects.get(stripe_checkout_session_id=session_id)
            if order.status == 'pending':
                session = stripe.checkout.Session.retrieve(session_id)
                if session.payment_status == 'paid':
                    order.status = 'completed'
                    order.stripe_payment_intent_id = session.payment_intent
                    order.save()
        except Order.DoesNotExist:
            pass
        except Exception:
            pass

    return render(request, 'core/checkout_success.html')


@login_required
def checkout_cancel(request):
    """Handle cancelled checkout."""
    return render(request, 'core/checkout_cancel.html')
